from django.db import models

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

