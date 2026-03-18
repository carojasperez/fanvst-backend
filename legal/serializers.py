from rest_framework import serializers
from legal.models import ComplaintBook
from adminsite.functions import validate_recaptcha


class ComplaintBookSer(serializers.ModelSerializer):
    gtoken = serializers.CharField(required=True)
    status_text = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ComplaintBook
        fields = '__all__'
        read_only_fields = ['status']

    def validate_gtoken(self, data):
        valid = validate_recaptcha(data)
        if valid==False:
            raise serializers.ValidationError(
                {'recaptcha': "Recaptcha Invalido"}
            )
        return True


