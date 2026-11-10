from collections import UserDict
from datetime import datetime, timedelta
from functools import wraps
import pickle

def input_error(func):
    """
    Декоратор для обробки помилок введення користувача.
    """
    
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found"
        except AttributeError:
            return "Contact not found"
        except IndexError:
            return "Enter the argument for the command"
    return inner


def parse_input(user_input):
    """
    Розбирає введений користувачем рядок на команду та аргументи.
    Повертає кортеж (command, *args).
    """

    cmd, *args = user_input.split()
    cmd = cmd.lower()
    return cmd, *args

class Field:
    """
    Клас, що представляє поле контакту.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    """
    Клас, що представляє телефонний номер контакту.
    """

    def __init__(self, value):
        if len(value) != 10 or not value.isdigit():
            raise ValueError("Phone number must be 10 digits long and contain only numbers.")
        super().__init__(value)

class Birthday(Field):
    """
    Клас, що представляє день народження контакту.
    """

    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y").date()    # Перевірка формату дати
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)

    @property
    def date(self):
        date = datetime.strptime(self.value, "%d.%m.%Y").date()
        return date

class Record:
    """
    Клас, що представляє запис контакту.
    """

    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {self.birthday if self.birthday else 'N/A'}"

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def remove_phone(self, phone):
        phone_to_remove = self.find_phone(phone)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)

    def edit_phone(self, old_phone, new_phone):
        new_phone = Phone(new_phone)
        phone_to_edit = self.find_phone(old_phone)
        if phone_to_edit is None:
            raise ValueError("Phone number not found.")
        i = self.phones.index(phone_to_edit)
        self.phones[i] = new_phone

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)


class AddressBook(UserDict):
    """
    Клас, що представляє адресну книгу.
    """

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        self.data.pop(name, None)

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []
        for record in self.data.values():
            if not record.birthday:
                continue

            birthday = record.birthday.date
            try:
                next_birthday = birthday.replace(year=today.year)
            except ValueError:
                # February 29 falls on February 28 in non-leap years.
                next_birthday = birthday.replace(year=today.year, day=28)

            if next_birthday < today:
                try:
                    next_birthday = birthday.replace(year=today.year + 1)
                except ValueError:
                    next_birthday = birthday.replace(year=today.year + 1, day=28)

            if (next_birthday - today).days > 7:
                continue

            congratulation_date = next_birthday
            if congratulation_date.weekday() == 5:
                congratulation_date += timedelta(days=2)
            elif congratulation_date.weekday() == 6:
                congratulation_date += timedelta(days=1)

            upcoming_birthdays.append({
                "name": record.name.value,
                "birthday": congratulation_date.strftime("%d.%m.%Y"),
            })

        return upcoming_birthdays

@input_error
def add_contact(args, book: AddressBook):
    """
    Додає новий контакт або оновлює існуючий.
    """

    name, phone, *_ = args
    record = book.find(name)

    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return "Contact added."
    record.add_phone(phone)
    
    return "Contact updated."

@input_error
def change_contact(args, book: AddressBook):
    """
    Змінює телефонний номер існуючого контакту.
    """

    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."

@input_error
def get_phone(args, book: AddressBook):
    """
    Показує телефонний номер контакту.
    """

    name, *_ = args
    record = book.find(name)
    if not record.phones:
        return f"{name} has no phone numbers."
    return f"Phone numbers for {name}: {', '.join(p.value for p in record.phones)}"

@input_error
def show_all_contacts(book: AddressBook):
    """
    Показує всі контакти.
    """

    if not book.data:
        return "Address book is empty."
    return str(book)

@input_error
def add_birthday(args, book: AddressBook):
    """
    Додає день народження контакту.
    """

    name, birthday, *_ = args
    record = book.find(name)
    record.add_birthday(birthday)
    return "Birthday added."

@input_error
def show_birthday(args, book: AddressBook):
    """
    Показує день народження контакту.
    """

    name, *_ = args
    record = book.find(name)
    if record.birthday is None:
        return "Birthday not set for this contact."
    return f"{name}'s birthday is on {record.birthday}"

@input_error
def show_birthdays(args, book: AddressBook):
    """
    Показує список контактів з наступними днями народження.
    """

    birthdays = book.get_upcoming_birthdays()
    if not birthdays:
        return "No upcoming birthdays in the next 7 days."
    else:
        return "\n".join(f"{b['name']} - {b['birthday']}" for b in birthdays)

def save_data(book, filename="addressbook.pkl"):
    """
    Зберігає адресну книгу у файл.
    """
    
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    """
    Завантажує адресну книгу з файлу.
    """

    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError):
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

def main():
    book = load_data()
    print("Welcome to the assistant bot!")

    try:
        while True:
            user_input = input("Enter a command: ")
            if not user_input.strip():
                continue
            command, *args = parse_input(user_input)

            if command in ["close", "exit"]:
                print("Good bye!")
                break

            elif command == "hello":
                print("How can I help you?")

            elif command == "add":
                print(add_contact(args, book))

            elif command == "change":
                print(change_contact(args, book))

            elif command == "phone":
                print(get_phone(args, book))

            elif command == "all":
                print(show_all_contacts(book))

            elif command == "add-birthday":
                print(add_birthday(args, book))

            elif command == "show-birthday":
                print(show_birthday(args, book))

            elif command == "birthdays":
                print(show_birthdays(args, book))

            else:
                print("Invalid command.")
    except (KeyboardInterrupt, EOFError):
        print("\nGood bye!")
    finally:
        save_data(book)


if __name__ == "__main__":
    main()