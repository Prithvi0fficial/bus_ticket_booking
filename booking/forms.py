from django import forms
from .models import Booking,Seat
class BookingForm(forms.ModelForm):
    seats = forms.ModelMultipleChoiceField(
        queryset=Seat.objects.filter(is_booked=False),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Booking
        fields = ['route', 'passenger_name', 'seats', 'date', 'passenger_email']

  #feedback

from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment', 'email']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
        }
      

