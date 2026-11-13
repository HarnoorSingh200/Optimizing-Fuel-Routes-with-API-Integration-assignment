from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from api.services.routing_service import routing_service
from api.services.fuel_service import fuel_service
from api.services.optimization_service import optimization_service, MAX_RANGE_MILES, MPG


@api_view(["GET", "POST"])
def fuel_plan(request):
    """
    POST /api/fuel-plan/

    Payload:
    {
        "start": "Key West, FL",
        "end": "Pensacola, FL",
        "max_range_miles": 500,  (optional, default: 500)
        "mpg": 10                (optional, default: 10)
    }
    """
    if request.method == "GET":
        return Response({
            "service": "Fuel Route Optimizer API",
            "version": "2.0",
            "status": "operational",
            "usage": "Send a POST request with 'start' and 'end' location strings.",
            "example_payload": {
                "start": "Key West, FL",
                "end": "Pensacola, FL",
                "max_range_miles": 500,
                "mpg": 10
            }
        })

    start = request.data.get("start")
    end = request.data.get("end")

    if not start or not end:
        return Response(
            {"error": "Both 'start' and 'end' parameters are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        max_range = float(request.data.get("max_range_miles", MAX_RANGE_MILES))
        mpg = float(request.data.get("mpg", MPG))
    except (ValueError, TypeError):
        max_range = MAX_RANGE_MILES
        mpg = MPG

    try:
        # Step 1 — Route calculation & polyline
        route_data = routing_service.get_route(start, end)

        # Step 2 — Spatial candidate pruning
        candidate_stations = fuel_service.get_candidate_stations(route_data)

        # Step 3 — Refueling schedule optimization & leg-by-leg accounting
        result = optimization_service.optimize(
            route_data,
            candidate_stations,
            max_range=max_range,
            mpg=mpg
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {
                "status": "error",
                "error": str(e),
                "message": "Failed to calculate optimal fuel route."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
