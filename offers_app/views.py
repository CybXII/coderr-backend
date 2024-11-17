from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.db.models import Q
from .models import Offer, OfferDetail
from .serializers import OfferSerializer, OfferDetailSerializer


class OfferPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class OfferAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = OfferPagination

    def get(self, request, pk=None):
        if pk:
            try:
                offer = Offer.objects.get(pk=pk)
                serializer = OfferSerializer(offer)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Offer.DoesNotExist:
                return Response({'error': 'Angebot nicht gefunden'}, status=status.HTTP_404_NOT_FOUND)
        else:
            offers = Offer.objects.all()

            # Filter: creator_id
            creator_id = request.query_params.get('creator_id')
            if creator_id:
                offers = offers.filter(user_id=creator_id)

            # Filter: min_price
            min_price = request.query_params.get('min_price')
            if min_price:
                try:
                    min_price = float(min_price)
                    offers = offers.filter(details__price__gte=min_price)
                except ValueError:
                    return Response({'error': 'min_price muss eine gültige Zahl sein.'}, status=status.HTTP_400_BAD_REQUEST)

            # Filter: max_delivery_time
            max_delivery_time = request.query_params.get('max_delivery_time')
            if max_delivery_time:
                try:
                    max_delivery_time = int(max_delivery_time)
                    offers = offers.filter(details__delivery_time_in_days__lte=max_delivery_time)
                except ValueError:
                    return Response({'error': 'max_delivery_time muss eine ganze Zahl sein.'}, status=status.HTTP_400_BAD_REQUEST)

            # Filter: search
            search = request.query_params.get('search')
            if search:
                offers = offers.filter(
                    Q(title__icontains=search) | Q(description__icontains=search)
                )

            # Sortierung: ordering
            ordering = request.query_params.get('ordering', 'updated_at')
            if ordering in ['updated_at', 'min_price']:
                offers = offers.order_by(ordering)
            else:
                # Standard-Sortierung, falls kein gültiger ordering-Wert vorhanden ist
                offers = offers.order_by('updated_at')

            # Pagination
            paginator = OfferPagination()
            result_page = paginator.paginate_queryset(offers, request)
            serializer = OfferSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
    def post(self, request):
        if request.user.type != 'business':
            return Response(
                {'error': 'Nur Business-Benutzer dürfen Angebote erstellen.'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        details = data.get('details', [])
        if len(details) != 3:
            return Response(
                {'error': 'Es müssen genau drei Details angegeben werden (basic, standard, premium).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer_types = [detail.get('offer_type') for detail in details]
        if sorted(offer_types) != ['basic', 'premium', 'standard']:
            return Response(
                {'error': 'Die Details müssen genau die Typen basic, standard und premium enthalten.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer = Offer.objects.create(
            user=request.user,
            title=data.get('title'),
            description=data.get('description'),
            image=data.get('image'),
        )

        for detail_data in details:
            if detail_data.get('revisions', 0) < -1:
                return Response(
                    {'error': 'Revisions müssen -1 (unbegrenzt) oder größer sein.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if detail_data.get('delivery_time_in_days', 0) <= 0:
                return Response(
                    {'error': 'Die Lieferzeit muss ein positiver Wert sein.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not detail_data.get('features', []):
                return Response(
                    {'error': 'Jedes Detail muss mindestens ein Feature enthalten.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            OfferDetail.objects.create(
                offer=offer,
                title=detail_data.get('title'),
                revisions=detail_data.get('revisions'),
                delivery_time_in_days=detail_data.get('delivery_time_in_days'),
                price=detail_data.get('price'),
                features=detail_data.get('features'),
                offer_type=detail_data.get('offer_type'),
            )

        return Response({
            "id": offer.id,
            "title": offer.title,
            "description": offer.description,
        }, status=status.HTTP_201_CREATED)

class OfferDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            try:
                detail = OfferDetail.objects.get(pk=pk)
                serializer = OfferDetailSerializer(detail)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except OfferDetail.DoesNotExist:
                return Response({'error': 'Angebotsdetail nicht gefunden'}, status=status.HTTP_404_NOT_FOUND)
        else:
            details = OfferDetail.objects.all()
            serializer = OfferDetailSerializer(details, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
