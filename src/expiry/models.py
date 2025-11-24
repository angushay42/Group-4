from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, date

class Item(models.Model):
    # define choice variables
    FRUIT = "FRUIT"
    DAIRY = "DAIRY"
    BREAD = "BREAD"
    VEGETABLES = "VEG"    # bug: any good?
    EGGS = "EGGS"
    MEAT = "MEAT"

    ITEM_CHOICES = {
        FRUIT:      "Fruit",
        DAIRY:      "Dairy",
        BREAD:      "Bread",
        VEGETABLES: "Vegetables",
        EGGS:       "Eggs",
        MEAT:       "Meat"
    }

    FRIDGE  = "FRDG"
    FREEZER = "FRZR"
    AMBIENT = "AMBI"

    STORAGE_TYPE_CHOICES = {
        FRIDGE:     "Fridge",
        FREEZER:    "Freezer",
        AMBIENT:    "Ambient"
    }

    # actual class attributes 
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    item_name = models.CharField(max_length=20)     # BUG: magic number
    expiry_date = models.DateField()                # todo: any params?
    entry_date = models.DateTimeField(
        db_default=models.functions.Now()
    )
    item_category = models.CharField(
        max_length=5,
        choices=ITEM_CHOICES,
    )
    storage_type = models.CharField(
        max_length=4,
        choices=STORAGE_TYPE_CHOICES
    )
