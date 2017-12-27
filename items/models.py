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
    name = models.CharField(verbose_name=_('Unit name'), max_length=50, null=False, blank=False, unique=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'), editable=False, blank=True)
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Modified date'), editable=False, blank=True)

    class Meta:
        verbose_name = _('Measure Units')
        verbose_name_plural = _('Measure Units')
        ordering = 'name'

    def __str__(self):
        return self.name


class MaterialAsset(models.Model):
    """This model represent assets at the warehouse. Any asset must have unique Part Number"""
    part_number = models.CharField(verbose_name=_('Part Number'), max_length=150, null=False,
                                   blank=False, unique=True)
    name = models.CharField(verbose_name=_('Name'), max_length=250, null=False, blank=False)
    measure_unit = models.ForeignKey(MeasureUnit, verbose_name=_('Measure Unit'), on_delete=models.PROTECT,
                                     null=False, blank=False, related_name='MaterialAsset')
    description = models.TextField(verbose_name=_('Description'), blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'), editable=False, blank=True)
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Modified date'), editable=False, blank=True)

    class Meta:
        verbose_name = _('Material Asset')
        verbose_name_plural = _('Material Assets')
        ordering = 'part_number', 'name'

    def __str__(self):
        return '{}, {} [{}]'.format(self.part_number, self.name, self.measure_unit.name)


class AmountConstraints(models.Model):
    """This model set minimum and max amount for assets for violations and notify"""
    material_asset = models.ForeignKey(MaterialAsset, verbose_name=_('Material Asset'), on_delete=models.PROTECT,
                                       related_name='Constraints', unique=True)
    # -1 - mean no minimal limitation
    _min_amount = models.BigIntegerField(verbose_name=_('Minimum Amount'), blank=True, null=False, default=-1)
    # -1 - mean no maximum limitation
    _max_amount = models.BigIntegerField(verbose_name=_('Maximum Amount'), blank=True, null=False, default=-1)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'), editable=False, blank=True)
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Modified date'), editable=False, blank=True)

    class Meta:
        verbose_name = _('Amount Constraints')
        verbose_name_plural = _('Amount Constraints')
        ordering = 'material_asset'

    @property
    def min_amount(self):
        if self._min_amount < 0:
            return inf
        else:
            return self._min_amount

    @min_amount.setter
    def min_amount(self, value):
        if isinf(value):
            self._min_amount = -1
        else:
            self._min_amount = value
        self.save()

    @property
    def max_amount(self):
        if self._max_amount < 0:
            return inf
        else:
            return self._max_amount

    @max_amount.setter
    def max_amount(self, value):
        if isinf(value):
            self._max_amount = -1
        else:
            self._max_amount = value
        self.save()

    def __str__(self):
        return '{} [{}:{}]'.format(self.material_asset.part_number, self.min_amount, self.max_amount)


class DocumentType(models.Model):
    """ This model represent document types, and set an amount direction"""
    TYPES = (
        (-1, _('Out')),
        (1, _('In')),
    )
    name = models.CharField(verbose_name=_('Type name'), max_length=50, blank=False, null=False, unique=True)
    # Just multiply amount and direction to get correct total amount
    direction = models.IntegerField(verbose_name=_('Direction'), choices=TYPES, null=False, blank=False)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'), editable=False, blank=True)
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Modified date'), editable=False, blank=True)

    class Meta:
        verbose_name = _('Document type')
        verbose_name_plural = _('Document types')
        ordering = 'name'

    def __str__(self):
        return '{} {}'.format(self.name, dict(self.TYPES)[self.direction])


class Warehouse(MPTTModel):
    """ This model represent several Warehouses.
        This can be a physical warehouse or virtual (transporting for example)
        Warehouse is MPTT model and could be have tree type structure"""
    name = models.CharField(verbose_name=_('Warehouse name'), max_length=50, blank=False, null=False, unique=True)
    parent = TreeForeignKey('self', null=True, blank=True, verbose_name=_('Parent'), related_name='children',
                            db_index=True, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'), editable=False, blank=True)
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Modified date'), editable=False, blank=True)

    class Meta:
        verbose_name = _('Warehouse')
        verbose_name_plural = _('Warehouses')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class ContractorGroup(MPTTModel):
    """ This model represent tree type structure of contractors"""
    name = models.CharField(verbose_name=_('Group name'), max_length=50, blank=False, null=False, unique=True)
    parent = TreeForeignKey('self', null=True, blank=True, verbose_name=_('Parent'), related_name='children',
                            db_index=True, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'), editable=False, blank=True)
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Modified date'), editable=False, blank=True)

    class Meta:
        verbose_name = _('Contractor')
        verbose_name_plural = _('Contractors')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class Contractor(models.Model):
    name = models.CharField(verbose_name=_('Contractor name'), max_length=100, blank=False, null=False)
    description = models.TextField(verbose_name=_('Description'), blank=True, null=True)
    address = models.TextField(verbose_name=_("Address"), blank=True, null=True)
    phone = models.TextField(verbose_name=_('Phone'), blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'), editable=False, blank=True)
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Modified date'), editable=False, blank=True)

    class Meta:
        verbose_name = _('Contractor')
        verbose_name_plural = _('Contractors')
        ordering = 'name'

    def __str__(self):
        return self.name


class Document(models.Model):
    """ This model represent operations with amounts"""
    document_type = models.ForeignKey(DocumentType, blank=False, null=False, verbose_name=_('Document type'),
                                      related_name='document', on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, blank=False, null=False, verbose_name=_('Warehouse'),
                                  related_name='document', on_delete=models.PROTECT)
    contractor = models.ForeignKey(Contractor, blank=False, null=False, verbose_name=_('Contractor'),
                                   related_name='document',  on_delete=models.PROTECT)
    description = models.TextField(verbose_name=_('Document name'), blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'), editable=False, blank=True)
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Modified date'), editable=False, blank=True)

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = 'modified', 'created'

    def __str__(self):
        return '{} {} {}'.format(self.document_type.name, self.contractor.name, self.modified)

    # TODO Подумать о операции перемещения товара между сладами.
    # TODO Создать другую модель с указанием складов (как считать общее количество товара?)
    # TODO exam next way. Creating two documents for moving assets in one transaction.atomic block
