from django import forms
from .models import LearningGoal
from django.utils import timezone

class LearningGoalForm(forms.ModelForm):
    class Meta:
        model = LearningGoal
        fields = ['title', 'description', 'target_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Master Django ORM & Model Relationships',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add details, topics to cover, or specific milestones...'
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
        }

    def clean_target_date(self):
        target_date = self.cleaned_data.get('target_date')
        return target_date
