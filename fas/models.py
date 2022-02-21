from django.db import models


class Flowlog(models.Model):
    hashkey = models.CharField(max_length=100, primary_key=True)
    src_app = models.CharField(max_length=20)
    dest_app = models.CharField(max_length=20)
    vpc_id = models.CharField(max_length=20)
    bytes_tx = models.IntegerField()
    bytes_rx = models.IntegerField()
    hour = models.IntegerField()
