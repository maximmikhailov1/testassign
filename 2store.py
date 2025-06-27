from datetime import date, timedelta, datetime
from typing import List, Optional, Dict


class Goods:
    """
    Базовый класс товара.
    """

    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity

    def __str__(self):
        return f"{self.name} (цена: {self.price:.2f}, кол-во: {self.quantity})"


class Food(Goods):
    """
    Продукт питания с БЖУ и калориями на 100г.
    """

    def __init__(self, name: str, price: float, quantity: int,
                 proteins: float, fats: float, carbs: float, calories: float):
        super().__init__(name, price, quantity)
        self.proteins = proteins
        self.fats = fats
        self.carbs = carbs
        self.calories = calories

    def __str__(self):
        return (f"{super().__str__()}, БЖУ: {self.proteins:.2f} / {self.fats:.2f} / {self.carbs:.2f}, "
                f"ккал: {self.calories}")


class Perishable(Goods):
    """
    Скоропортящийся товар с датой создания и сроком годности.
    """

    def __init__(self, name: str, price: float, quantity: int,
                 creation_date: date, shelf_life_days: int):
        super().__init__(name, price, quantity)
        self.creation_date = creation_date
        self.shelf_life_days = shelf_life_days

    def expiration_date(self) -> date:
        return self.creation_date + timedelta(days=self.shelf_life_days)

    def time_to_expire(self) -> timedelta:
        expiration_midnight = datetime.combine(self.expiration_date(), datetime.min.time())
        return expiration_midnight - datetime.now()

    def is_expired(self) -> bool:
        return self.time_to_expire() <= timedelta(0)

    def expires_in_less_than(self, delta: timedelta) -> bool:
        return self.time_to_expire() < delta

    def __str__(self):
        exp_date = self.expiration_date().strftime("%d-%m-%Y")
        return f"{super().__str__()}, срок годности до: {exp_date}"


class Vitamins(Goods):
    """
    Витамины с признаком отпуска без рецепта.
    """

    def __init__(self, name: str, price: float, quantity: int, without_prescription: bool):
        super().__init__(name, price, quantity)
        self.without_prescription = without_prescription

    def __str__(self):
        wp = "без рецепта" if self.without_prescription else "требуется рецепт"
        return f"{super().__str__()}, {wp}"


class CombinedProduct(Goods):
    """
    Товар, который может быть одновременно Food и Perishable и/или Vitamins.
    """

    def __init__(self, name: str, price: float, quantity: int,
                 food: Optional[Food] = None,
                 perishable: Optional[Perishable] = None,
                 vitamins: Optional[Vitamins] = None):
        super().__init__(name, price, quantity)
        self.food = food
        self.perishable = perishable
        self.vitamins = vitamins

    def is_food(self):
        return self.food is not None

    def is_perishable(self):
        return self.perishable is not None

    def is_vitamins(self):
        return self.vitamins is not None

    def __str__(self):
        parts = [f"{self.name} (цена: {self.price:.2f}, кол-во: {self.quantity})"]
        if self.is_food():
            parts.append(
                f"БЖУ: {self.food.proteins:.2f}/{self.food.fats:.2f}/{self.food.carbs:.2f}, ккал: {self.food.calories}")
        if self.is_perishable():
            exp = self.perishable.expiration_date().strftime("%d-%m-%Y")
            parts.append(f"Срок годности: до {exp}")
        if self.is_vitamins():
            wp = "без рецепта" if self.vitamins.without_prescription else "требуется рецепт"
            parts.append(wp)
        return "; ".join(parts)


class Storage:
    """
    Управление складом.
    """

    def __init__(self):
        self.products: Dict[str, CombinedProduct] = {}

    def add_product(self, product: CombinedProduct):
        if product.name in self.products:
            # Обновляем количество
            self.products[product.name].quantity += product.quantity
        else:
            # Добавляем новый продукт
            self.products[product.name] = product

    def get_product(self, name: str) -> Optional[CombinedProduct]:
        return self.products.get(name)

    def list_products(self) -> List[CombinedProduct]:
        return list(self.products.values())

    def products_to_restock(self, threshold: int = 5) -> List[CombinedProduct]:
        return [p for p in self.products.values() if p.quantity < threshold]

    def products_to_dispose(self) -> List[CombinedProduct]:
        to_dispose = []
        for p in self.products.values():
            if p.is_perishable():
                if p.perishable.is_expired():
                    to_dispose.append(p)
        return to_dispose


class Cart:
    """
    Корзина пользователя.
    """

    def __init__(self, storage: Storage):
        self.storage = storage
        # Словарь: имя товара -> количество
        self.items: Dict[str, int] = {}
        # Пользовательские нормы БЖУ и калорий
        self.norm_proteins = None
        self.norm_fats = None
        self.norm_carbs = None
        self.norm_calories = None

    def set_norms(self, proteins: float, fats: float, carbs: float, calories: float):
        self.norm_proteins = proteins
        self.norm_fats = fats
        self.norm_carbs = carbs
        self.norm_calories = calories

    def add_item(self, product_name: str, quantity: int, has_prescription: bool = False) -> List[str]:
        """
        Добавляет товар в корзину с проверками.
        :returns: Список причин по которым продукт не был продан.
        """
        warnings = []

        product = self.storage.get_product(product_name)
        if product is None:
            warnings.append(f"Товар '{product_name}' отсутствует на складе.")
            return warnings

        if quantity > product.quantity:
            warnings.append(
                f"Товара '{product_name}' на складе недостаточно (запрошено {quantity}, есть {product.quantity}).")

        """
        Продажи витаминов
        w_p h_p  f
        0   0   0
        0   1   1
        1   0   1
        1   1   x
        """
        if product.is_vitamins() and not (product.vitamins.without_prescription or has_prescription):
            warnings.append(f"Витамины '{product_name}' нельзя отпускать без рецепта.")

        # Проверяем срок годности, до конца >= 24 часа
        if product.is_perishable():
            if product.perishable.expires_in_less_than(timedelta(hours=24)):
                warnings.append(f"Товар '{product_name}' испортится менее чем через 24 часа и не может быть продан.")

        # Если предупреждений нет, добавляем в корзину
        if not warnings:
            self.items[product_name] = self.items.get(product_name, 0) + quantity
            self.storage.products[product_name].quantity -= quantity

        return warnings

    def total_cost(self) -> float:
        """
        :returns: Стоимость товаров в корзине
        """
        cost = 0.0
        for name, qty in self.items.items():
            product = self.storage.get_product(name)
            if product:
                cost += product.price * qty
        return cost

    def total_bju_calories(self):
        """
        Суммирует БЖУ и калории в корзине.
        Если товар не является food, считает 0.
        :returns: Кортеж (белки, жиры, углеводы, калории)
        """
        proteins = fats = carbs = calories = 0.0
        for name, qty in self.items.items():
            product = self.storage.get_product(name)
            if product and product.is_food():
                proteins += product.food.proteins * qty
                fats += product.food.fats * qty
                carbs += product.food.carbs * qty
                calories += product.food.calories * qty
        return proteins, fats, carbs, calories

    def check_norms(self) -> List[str]:
        """
        Проверяет превышение норм БЖУ и калорий.
        :returns: Список предупреждений.
        """
        warnings = []
        if None in (self.norm_proteins, self.norm_fats, self.norm_carbs, self.norm_calories):
            # Нормы не установлены
            return warnings

        proteins, fats, carbs, calories = self.total_bju_calories()

        if proteins > self.norm_proteins:
            warnings.append(f"Превышен уровень белков: {proteins:.2f} > {self.norm_proteins:.2f}")
        if fats > self.norm_fats:
            warnings.append(f"Превышен уровень жиров: {fats:.2f} > {self.norm_fats:.2f}")
        if carbs > self.norm_carbs:
            warnings.append(f"Превышен уровень углеводов: {carbs:.2f} > {self.norm_carbs:.2f}")
        if calories > self.norm_calories:
            warnings.append(f"Превышен уровень калорий: {calories:.2f} > {self.norm_calories:.2f}")

        return warnings

    def clear(self):
        self.items.clear()


if __name__ == "__main__":
    st = Storage()

    st.add_product(CombinedProduct(
        name="Яблоко",
        price=50,
        quantity=100,
        food=Food("Яблоко", 50, 100, proteins=0.3, fats=0.2, carbs=14, calories=52)
    ))

    st.add_product(CombinedProduct(
        name="Молоко",
        price=80,
        quantity=50,
        food=Food("Молоко", 80, 50, proteins=3.2, fats=3.5, carbs=4.8, calories=60),
        perishable=Perishable("Молоко",
                              80,
                              50,
                              creation_date=(date.today() - timedelta(days=3)),
                              shelf_life_days=3)
    ))
    st.add_product(CombinedProduct(
        name="Хлеб",
        price=80,
        quantity=50,
        food=Food("Хлеб", 80, 50, proteins=3.2, fats=3.5, carbs=4.8, calories=60),
        perishable=Perishable("Хлеб",
                              80,
                              50,
                              creation_date=(date.today() - timedelta(days=3)),
                              shelf_life_days=4)
    ))

    st.add_product(CombinedProduct(
        name="Витамин C",
        price=300,
        quantity=20,
        vitamins=Vitamins("Витамин C", 300, 20, without_prescription=True)
    ))

    cart = Cart(st)
    cart.set_norms(proteins=10, fats=10, carbs=50, calories=500)
    # 100 яблок 1 молоко 19 витаминов C
    warnings = cart.add_item("Яблоко", 100)
    warnings += cart.add_item("Молоко", 1)
    warnings += cart.add_item("Витамин C", 19, has_prescription=False)

    print("Предупреждения при добавлении в корзину:")
    for w in warnings:
        print("-", w)

    print(f"Общая стоимость: {cart.total_cost():.2f}\n")

    b, f, c, cal = cart.total_bju_calories()
    print(f"Суммарные БЖУ и калории: Белки={b:.2f}, Жиры={f:.2f}, Углеводы={c:.2f}, Калории={cal}")

    norm_warnings = cart.check_norms()
    if norm_warnings:
        print("Предупреждения по нормам:")
        for w in norm_warnings:
            print("-", w)
    else:
        print("Нормы БЖУ и калорий не превышены.")

    print("\nТовары для закупки (кол-во < 5):")
    for p in st.products_to_restock():
        print("-", p)

    print("\nТовары, которые необходимо утилизировать:")
    for p in st.products_to_dispose():
        print("-", p)
