from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Theater, Seat, Booking
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db import transaction

def movie_list(request):
    search_query = request.GET.get('search')
    if search_query:
        movies = Movie.objects.filter(name__icontains=search_query)
    else:
        movies = Movie.objects.all()
    return render(request, 'movies/movie_list.html', {'movies': movies})

def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theaters = Theater.objects.filter(movie=movie)
    return render(request, 'movies/theater_list.html', {'movie': movie, 'theaters': theaters})



@login_required(login_url='/login/')
def book_seats(request, theater_id):
    theaters = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theaters)
    if request.method == 'POST':
        selected_seats = request.POST.getlist('seats')
        error_seats = []
        if not selected_seats:
            return render(request, 'movies/seat_selection.html', {
                'theaters': theaters,
                'seats': seats,
                'error': 'No seat selected',
            })
        for seat_id in selected_seats:
            try:
                with transaction.atomic():
                    seat = Seat.objects.select_for_update().get(id=seat_id, theater=theaters)
                    if seat.is_booked:
                        error_seats.append(seat.seat_number)
                        continue
                    Booking.objects.create(
                        user=request.user,
                        seat=seat,
                        movie=theaters.movie,
                        theater=theaters,
                    )
                    seat.is_booked = True
                    seat.save(update_fields=['is_booked'])
            except (Seat.DoesNotExist, IntegrityError):
                error_seats.append(str(seat_id))
        if error_seats:
            error_message = f"The following seats are already booked: {', '.join(error_seats)}"
            seats = Seat.objects.filter(theater=theaters)
            return render(request, 'movies/seat_selection.html', {
                'theaters': theaters,
                'seats': seats,
                'error': error_message,
            })
        return redirect('profile')
    return render(request, 'movies/seat_selection.html', {'theaters': theaters, 'seats': seats})

