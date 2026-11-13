import math
from unittest.mock import patch
from django.test import TestCase, SimpleTestCase
from rest_framework.test import APIClient
from rest_framework import status

from api.services.optimization_service import OptimizationService
from api.services.fuel_service import fuel_service


class OptimizationServiceUnitTests(SimpleTestCase):
    """Unit tests for spatial mathematics and fuel stop optimization solver."""

    def setUp(self):
        self.optimizer = OptimizationService()

    def test_haversine_distance_identity(self):
        """Distance between a point and itself must be 0.0 miles."""
        p = (24.5551, -81.7800)  # Key West
        d = self.optimizer.distance(p, p)
        self.assertAlmostEqual(d, 0.0, places=4)

    def test_haversine_distance_known_geodesic(self):
        """Verify distance between Key West, FL and Miami, FL is ~130 miles."""
        key_west = (24.5551, -81.7800)
        miami = (25.7617, -80.1918)
        d = self.optimizer.distance(key_west, miami)
        self.assertTrue(120 < d < 140, f"Expected ~130 miles, got {d}")

    def test_cumulative_distances_monotonic(self):
        """Cumulative distance array must be strictly increasing and start with 0."""
        route = [
            (24.5551, -81.7800),
            (25.0865, -80.4473),
            (25.7617, -80.1918),
        ]
        cum_dist = self.optimizer.cumulative_distances(route)
        self.assertEqual(len(cum_dist), len(route))
        self.assertEqual(cum_dist[0], 0.0)
        self.assertTrue(cum_dist[0] < cum_dist[1] < cum_dist[2])

    def test_calculate_total_cost_zero_stops(self):
        """When 0 stops are made on short trip, baseline departure tank rate applies."""
        cost = self.optimizer.calculate_total_cost(200.0, [])
        # 200 / 10 = 20 gallons * 3.5 = $70.00
        self.assertEqual(cost, 70.0)

    def test_calculate_total_cost_with_stops(self):
        """Verify exact leg-by-leg cost calculation with refueling stops."""
        stops = [
            {
                "stop_number": 1,
                "name": "Stop 1",
                "price": 3.00,
                "distance_from_start_miles": 300.0,
                "cost_usd": 90.0,  # 30 gal * $3.00
            }
        ]
        # Total dist = 500 mi. Last stop is at 300 mi.
        # Remaining leg = 200 mi / 10 mpg = 20 gal * $3.00 = $60.00
        # Total cost = 90.0 + 60.0 = $150.00
        cost = self.optimizer.calculate_total_cost(500.0, stops)
        self.assertEqual(cost, 150.0)

    def test_corridor_filtering_projects_distance(self):
        """Corridor filtering must attach route_distance_miles and filter outliers."""
        route = [
            (24.5551, -81.7800),
            (25.7617, -80.1918),
            (28.5383, -81.3792),
        ]
        stations = [
            # Near route
            {"station_id": 1, "name": "Near Stop", "latitude": 25.76, "longitude": -80.19, "price": 3.20},
            # Far away (California)
            {"station_id": 2, "name": "Far Stop", "latitude": 34.05, "longitude": -118.24, "price": 4.50},
        ]
        near = self.optimizer.stations_near_route(route, stations, max_corridor_miles=20.0)
        self.assertEqual(len(near), 1)
        self.assertEqual(near[0]["station_id"], 1)
        self.assertIn("route_distance_miles", near[0])


class FuelPlanAPITests(TestCase):
    """Integration tests for the REST API endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_get_api_usage(self):
        """GET /api/fuel-plan/ returns operational status and schema instructions."""
        res = self.client.get("/api/fuel-plan/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("status"), "operational")

    def test_missing_start_or_end_returns_400(self):
        """POST /api/fuel-plan/ without start or end must return 400 Bad Request."""
        res = self.client.post("/api/fuel-plan/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    def test_missing_end_returns_400(self):
        res = self.client.post("/api/fuel-plan/", {"start": "Miami, FL"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("api.views.routing_service.get_route")
    def test_successful_fuel_plan_response(self, mock_get_route):
        """Mock external ORS route and verify optimal fuel plan API output."""
        mock_get_route.return_value = {
            "distance_miles": 841.2,
            "geometry": "k|ztC~scrN_~hW_hmAwwnJrdsb@",
            "start_coords": (24.5551, -81.7800),
            "end_coords": (30.4213, -87.2169),
        }

        payload = {
            "start": "Key West, FL",
            "end": "Pensacola, FL",
            "max_range_miles": 500,
            "mpg": 10
        }

        res = self.client.post("/api/fuel-plan/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("status"), "success")
        self.assertIn("distance_miles", res.data)
        self.assertIn("stops", res.data)
        self.assertIn("total_cost", res.data)
        self.assertEqual(res.data["distance_miles"], 841.2)
