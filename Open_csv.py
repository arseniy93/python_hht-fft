import csv

class Open_csv:
    def __init__(self, file_path):
        """
        Инициализирует объект CSVReader.
        Args:
            file_path (str): Путь к CSV файлу.
        """
        self.file_path = file_path

        self.times_list = list()
        self.amplitude_list = list()
        self.step_by_time = 0.

    def set_path(self, file_path):
        self.file_path = file_path

    def get_path(self):
        return self.file_path

    """
    Класс для чтения CSV файлов.
    """

    def __read_data(self, delimiter=',', quotechar='"'):
        """
        Читает данные из CSV файла.

        Args:
            delimiter (str, optional): Разделитель полей. Defaults to ','.
            quotechar (str, optional): Символ кавычек. Defaults to '"'.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=delimiter, quotechar=quotechar)
                return list(reader)
        except FileNotFoundError:
            print(f"Файл не найден: {self.file_path}")
            self.data = []
            self.header = []
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            self.data = []
            self.header = []

    def calculcated_all_lists(self):
        self.__get_list_of_amplitudes()
        self.__get_list_of_times()


    def __get_list_of_amplitudes(self):
        for raw in self.__read_data():
            if raw[0] == "Sample Interval":
                self.step_by_time = float(raw[1])
            self.amplitude_list.append(raw[4])
        self.amplitude_list = list(map(float, self.amplitude_list))
        # return self.amplitude_list

    def __get_list_of_times(self):
        if len(self.amplitude_list) == 0:
            raise Exception("сперва нужно получить амплитуду")
        else:
            for x in range(len(self.amplitude_list) ):
                self.times_list.append(x * self.step_by_time)
            return self.times_list



