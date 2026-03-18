'''
Serializer for Location and Locality Models
'''
from rest_framework import serializers
from adminsite.baseinfo.models import (Country, Department, Province, Membership,
                                       District, Bank, Category, SubCategory)
from django.contrib.auth.models import User


class DepartmentSer(serializers.ModelSerializer):
    # country = CountrySer(read_only=True)

    class Meta:
        model = Department
        fields = ('id', 'name')


class ProvinceSer(serializers.ModelSerializer):
    # department = DepartmentSer(read_only=True, many=False)
    class Meta:
        model = Province
        fields = ('id', 'name')


class DistrictSer(serializers.ModelSerializer):
    province = ProvinceSer(read_only=False)

    class Meta:
        model = District
        fields = ('id', 'name', 'province')


class BankSer(serializers.ModelSerializer):
    
    class Meta:
        model = Bank
        fields = ('id', 'name')


class CategorySer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'description')


class SubCategorySer(serializers.ModelSerializer):
    category = CategorySer(read_only=True)
    class Meta:
        model = SubCategory
        fields = ('id', 'name', 'category')


class CountrySer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'iso3166', 'name')


class MembershipSer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('name', 'percent')
