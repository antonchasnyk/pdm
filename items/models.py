from django.contrib.auth.models import User
from django.db import models
from django.urls.base import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
from math import inf, isinf
from mptt.models import MPTTModel, TreeForeignKey

# Create your models here.


class MeasureUnit(models.Model):
    """This model represent list of possible measure units"""
    Name = models.CharField(verbose_name=_('Unit name'), max_length=50, null=False, blank=False, unique=True)

    class Meta:
        verbose_name = _('Measure Units')
        verbose_name_plural = _('Measure Units')
        ordering = 'Name'

    def __str__(self):
        return self.Name


class MaterialAsset(models.Model):
    """This model represent assets at the warehouse. Any asset must have unique Purt Number"""
    PartNumber = models.CharField(verbose_name=_('Part Number'), max_length=150, null=False,
                                      blank=False, unique=True)
    Name = models.CharField(verbose_name=_('Name'), max_length=250, null=False, blank=False)
    Unit = models.ForeignKey(MeasureUnit, verbose_name=_('Measure Unit'), on_delete=models.PROTECT,
                             null=False, blank=False, related_name='MaterialAsset')
    Description = models.TextField(verbose_name=_('Description'), blank=True, null=True)

    class Meta:
        verbose_name = _('Material Asset')
        verbose_name_plural = _('Material Assets')
        ordering = 'PartNumber', 'Name'

    def __str__(self):
        return '{}, {} [{}]'.format(self.PartNumber, self.Name, self.Unit.Name)


class AmountConstraints(models.Model):
    """This model set minimum and max amount for assets for violations and notify"""
    Asset = models.ForeignKey(MaterialAsset, verbose_name=_('Material Asset'), on_delete=models.PROTECT,
                              related_name='Constraints', unique=True)
    # -1 - mean no minimal limitation
    _MinAmount = models.BigIntegerField(verbose_name=_('Minimum Amount'), blank=True, null=False, default=-1)
    # -1 - mean no maximum limitation
    _MaxAmount = models.BigIntegerField(verbose_name=_('Maximum Amount'), blank=True, null=False, default=-1)

    class Meta:
        verbose_name = _('Amount Constraints')
        verbose_name_plural = _('Amount Constraints')
        ordering = 'Asset'

    @property
    def MinAmount(self):
        if self._MinAmount < 0:
            return inf
        else:
            return self._MinAmount

    @MinAmount.setter
    def MinAmount(self, value):
        if isinf(value):
            self._MinAmount = -1
        else:
            self._MinAmount = value
        self.save()

    @property
    def MaxAmount(self):
        if self._MaxAmount < 0:
            return inf
        else:
            return self._MaxAmount


    @MaxAmount.setter
    def MaxAmount(self, value):
        if isinf(value):
            self._MaxAmount = -1
        else:
            self._MaxAmount = value
        self.save()

    def __str__(self):
        return '{} [{}:{}]'.format(self.Asset.PartNumber, self.MinAmount, self.MaxAmount)


class DocumentType(models.Model):
    """ This model represent document types, and set an amount direction"""
    TYPES = (
        (-1, _('Out')),
        (1, _('In')),
    )
    Name = models.CharField(verbose_name=_('Type name'), max_length=50, blank=False, null=False, unique=True)
    # Just multiply amount and direction to get correct total amount
    Direction = models.IntegerField(verbose_name=_('Direction'), choices=TYPES, null=False, blank=False)

    class Meta:
        verbose_name = _('Document type')
        verbose_name_plural = _('Document types')
        ordering = 'Name'

    def __str__(self):
        return '{} {}'.format(self.Name, dict(self.TYPES)[self.Direction])


class Warehouse(MPTTModel):
    """ This model represent several Warehouses.
        This can be a physical warehouse or virtual (transporting for example)
        Warehouse is MPTT model and could be have tree type structure"""
    Name = models.CharField(verbose_name=_('Warehouse name'), max_length=50, blank=False, null=False, unique=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            on_delete=models.PROTECT)

    class Meta:
        verbose_name = _('Warehouse')
        verbose_name_plural = _('Warehouses')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.Name


class Document(models.Model):
    """ This model represent possible operations this items"""
    # TODO Подумать о операции перемещения товара между сладами.
    # TODO Создать другую модель с указанием складов (как считать общее количество товара?)


