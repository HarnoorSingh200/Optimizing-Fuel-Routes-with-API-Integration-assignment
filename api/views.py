from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from api.services.routing_service import routing_service
from api.services.fuel_service import fuel_service
from api.services.optimization_service import optimization_service


@api_view(["POST"])
def fuel_plan(request):
    """
    POST /api/fuel-plan/

    Body:
    {
        "start": "Key West, FL",
        "end": "Pensacola, FL"
    }
    """

    start = request.data.get("start")
    end = request.data.get("end")

    if not start or not end:
        return Response(
            {"error": "start and end are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Step 1 — route
        route_data = routing_service.get_route(start, end)

        # Step 2 — stations
        stations = fuel_service.get_candidate_stations(route_data)

        # Step 3 — optimization
        result = optimization_service.optimize(route_data, stations)

        return Response(result)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
