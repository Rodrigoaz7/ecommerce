from django.db import models
from django.conf import settings
from catalogo.models import Product
from pagseguro import PagSeguro

class CartItemManager(models.Manager):

	def add_item(self, cart_key, product):
		#Se já existir um produto no carrinho, então apenas aumentamos a quantidade
		if self.filter(cart_key=cart_key, product=product).exists():
			created = False
			cart_item = self.get(cart_key=cart_key, product=product)
			cart_item.quantity = cart_item.quantity + 1
			cart_item.save()
		else: #Se não existir, adicionamos este produto ao carrinho
			created = True
			cart_item = CartItem.objects.create(cart_key=cart_key, product=product, price=product.price)	
		return cart_item, created

class CartItem(models.Model):

	cart_key = models.CharField('Chave do Carrinho', max_length=40, db_index=True)  #id do carrinho
	product = models.ForeignKey('catalogo.Product', verbose_name='Produto')
	quantity = models.PositiveIntegerField('Quantidade', default=1)
	price = models.DecimalField('Preço', decimal_places=2, max_digits=8)

	objects = CartItemManager()

	class Meta:
		verbose_name = 'Item do carrinho'
		verbose_name_plural = 'Itens dos carrinhos'
		unique_together = (('cart_key', 'product'), ) #Código para garantir que um produto seja único no carrinho 

	def __str__(self):
		return '{} [{}]'.format(self.product, self.quantity)


class OrderManager(models.Manager):

	def create_order(self, user, cart_items):
		order = self.create(user=user)
		for cart_item in cart_items:
			ordem_item = OrderItem.objects.create(
				order=order, quantity=cart_item.quantity, product=cart_item.product,
				price=cart_item.price
			)
		return order


# classe dos pedidos de compras
class Order(models.Model):

	STATUS_CODE = (
		(0, 'Aguardando pagamento'),
		(1, 'Compra concluída'),
		(2, 'Compra cancelada')
	)

	#Opções de pagamento
	PAYMENT_OPTION_CHOICES = (
		('deposit', 'Depósito'),
		('pagseguro', 'PagSeguro'),
		('paypal', 'Paypal'),
	)

	user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Usuário')
	status = models.IntegerField(
		'Situação', choices=STATUS_CODE, default = 0, blank = True
	) 
	payment_option = models.CharField(
		'Opção de pagamento', choices=PAYMENT_OPTION_CHOICES, max_length=20, default='deposit'
	)

	created = models.DateTimeField('Criado em ', auto_now_add=True)
	modified = models.DateTimeField('Modificado em ', auto_now=True)

	objects = OrderManager()

	class Meta:
		verbose_name = 'Pedido'
		verbose_name_plural = 'Pedidos'

	def __str__(self):
		return 'Pedido #{}'.format(self.pk)

	def products(self):
		products_ids = self.items.values_list('product')
		return Product.objects.filter(pk__in=products_ids)

	def total(self):
		aggregate_queryset = self.items.aggregate(
			total = models.Sum(
				models.F('price') * models.F('quantity'),
				output_field = models.DecimalField()
			)
		)

		return aggregate_queryset['total']

	def pagseguro_update_status(self, status):
		if status == '3':
			self.status = 1
		elif status == '7':
			self.status == 2
		self.save()

	def pagseguro(self):
		pg = PagSeguro(
			email = settings.PAGSEGURO_EMAIL, token=settings.PAGSEGURO_TOKEN, 
			config = {'sandbox': settings.PAGSEGURO_SANDBOX}
		)
		pg.sender = {
			'email': self.user.email
		}
		pg.reference_prefix = None
		pg.shipping = None
		pg.reference = self.pk
		for item in self.items.all():
			pg.items.append(
				{
					'id': item.product.pk,
					'description': item.product.name,
					'quantity': item.quantity,
					'amount': '%.2f' % item.price
				}
			)
			return pg


#Classe para exibição dos itens dos pedidos
class OrderItem(models.Model):
	order = models.ForeignKey(Order, verbose_name='Pedido', related_name='items')
	product = models.ForeignKey('catalogo.Product', verbose_name='Produto')
	quantity = models.PositiveIntegerField('Quantidade', default=1)
	price = models.DecimalField('Preço', decimal_places=2, max_digits=8)

	class Meta:
		verbose_name = 'Item do pedido'
		verbose_name_plural = 'Itens dos pedidos'


#Função de disparo de sinais (Deletar objeto com quantidade=0)
def post_save_cart_item(instance, **kwargs):
	if instance.quantity < 1:
		instance.delete()

models.signals.post_save.connect(
	post_save_cart_item, sender=CartItem, dispatch_uid='post_save_cart_item'
)
