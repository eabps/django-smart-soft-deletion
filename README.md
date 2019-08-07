# **Django Smart SoftDeletion** #
>* **Em Desenvolvimento!**
>* **Ainda não disponível no PyPi**

_Django Smart SoftDeletion_ é um package para implementação de _Soft Deletion_ em projetos desenvolvidos com Django Web Framework.

Caso queira testar os conceitos deste trabalho em seu projeto, faça:

## **Instalação** ##
1. Copie a app _smart_soft_deletion_ para o diretório de apps de seu projeto;
2. Adicione _'smart_soft_deletion_ ao `INSTALLED_APPS`:
```py
INSTALLED_APPS = [
    # ...
    'smart_soft_deletion.apps.SmartSoftDeletionConfig',
]
```

## **Exemplo de Uso** ##
Para que um _model class_ implemente soft deletion, basta que o mesmo herde de `smart_soft_deletion.models.SoftDeletionMixin`

O exemplo abaixo implementa quatro classes. Todas herdeiras de `SoftDeletionMixin`:
* Country
* Founder
* Industry - Possui ForeignKey para **Contry** e Possui ManyToMany para **Founder**
* Product - Possui ForeignKey para **Industry**

```py
# models.py
from django.db import models

from smart_soft_deletion.models import SoftDeletionMixin


class Country(SoftDeletionMixin):
    name = models.CharField(max_length=64, unique=True, verbose_name="Name")

    def __str__(self):
        return "{}".format(self.name)


class Founder(SoftDeletionMixin):
    name = models.CharField(max_length=128, unique=True, verbose_name="Name")

    def __str__(self):
        return "{}".format(self.name)


class Industry(SoftDeletionMixin):
    name = models.CharField(max_length=128, unique=True, verbose_name="Name")
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL, verbose_name="Country")
    founders = models.ManyToManyField(Founder, verbose_name="Founders")

    def __str__(self):
        return "{}".format(self.name)


class Product(SoftDeletionMixin):
    name = models.CharField(max_length=128, unique=True, verbose_name="Name")
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, verbose_name="Industry")

    def __str__(self):
        return "{}".format(self.name)
```

### **Criando Objetos** ###
Criando objetos
```py
# import Contry, Founder, Industry, Product

# create country
usa = Country.objects.create(name="USA")
japan = Country.objects.create(name="Japan")

# create founder
bill_gates = Founder.objects.create(name="Bill Gates")
paul_allen = Founder.objects.create(name="Paul Allen")
akio_morita = Founder.objects.create(name="Akio Morita")

# create industry
microsoft = Industry.objects.create(name="Microsoft", country=usa)
sony = Industry.objects.create(name="Sony", country=japan)
        
microsoft.founders.add(bill_gates)
microsoft.founders.add(paul_allen)
sony.founders.add(akio_morita)

# create product
xbox = Product.objects.create(name="Xbox", industry=microsoft)
play_station = Product.objects.create(name="Play Station", industry=sony)
```
### **Deletando e Recuperando Objetos** ###
```py
# continua...

Product.objects.all()
# <SoftDeletionQuerySet [<Product: Xbox>, <Product: Play Station>]>

play_station.delete()
Product.objects.all()
# <SoftDeletionQuerySet [<Product: Xbox>]>

Product.objects_with_deleted.all()
# <SoftDeletionQuerySet [<Product: Xbox>, <Product: Play Station>]>
# Isso porque objects_with_deleted manager inclui na queryset os objetos deletados

play_station = Product.objects_with_deleted.get(name='Play Station')
play_station.is_deleted
# True
play_station.restore()
play_station.is_deleted
# False
Product.objects.all()
# <SoftDeletionQuerySet [<Product: Xbox>, <Product: Play Station>]>
# Isso porque o metodo restore recupera o objeto deletado e por consequencia o mesmo volta a aparecer na queryset do manager objects 
```
**Deletando um objeto ForeignKey CASCADE.**

`play_station` tem um ForeignKey CASCADE para `microsoft`. No exemplo abaixo o objeto microsoft será deletado e depois restaurado.
```py
# continua...

microsoft.delete()
Product.objects.all()
# <SoftDeletionQuerySet [<Product: Play Station>]>
# xbox foi deletado em cascade junto com microsoft

microsoft.restore()
Product.objects.all()
# <SoftDeletionQuerySet [<Product: Play Station>]>
# xbox não foi restaurado pois objetos deletados em cascade não são restaurados quando seu foreign key é restaurado. Para restaurar xbox faça: xbox.restore(). Veja o item 2 da sessão 'O que ainda falta'
```
**Deletando um objeto ForeignKey SET_NULL.**

`microsoft` tem um ForeignKey SET_NULL para `usa`. No exemplo abaixo o objeto usa será deletado e depois restaurado.
```py
# continua...

microsoft.country
# <Country: USA>

usa.delete()
microsoft.refresh_from_db()
microsoft.is_deleted
# False
#Isso porque objetos com foreign key SET_NULL não são deletados em cascata quando o objeto foreign key é deletado

microsoft.country
# None
# O field foreign key recebe valor None quando o objeto foreign key é deletado

usa.restore()
microsoft.refresh_from_db()
microsoft.country
# O field microsoft.country não recupera a relação com o foreign key restaurado. Veja o item 3 da sessão 'O que ainda falta'
```

**Deletando um objeto ForeignKey ManyToMany.**
```py
# continua

microsoft.founders.all()
# Veja ítem 4 de 'O que ainda falta'

paul_allen.delete()
microsoft.founders.all()
# Veja ítem 4 de 'O que ainda falta'

paul_allen.restore()
microsoft.founders.all()
# Veja ítem 4 de 'O que ainda falta'
```


Para fazer um **hard deletion**, acrescente o parametro `hard_deletion=True` no método `delete()`. Exemplo:
```py
# continua

usa.delete(hard_deletion=True)
```

## **O que ainda falta** ##
1. Implementar comportamento para `on_delete=models.SET`
2. Implementar restore de objetos que foram deletado em cascade qndo seu foreign key for restaurado. Esta funcionalide deve poupar os objetos que não foram deletados via CASCADE;
3. Implementar restauração da ligação foreign key com fields SET_NULL quando o objeto foreign key for restaurado. Esta funcionalidade de poupar objetos que não perderam a ligação por ocasião de um delete do foreignkey;
4. Evitar que um objeto com ManyToMany ao ser deletado perca a relação com os objetos foreign keys;
