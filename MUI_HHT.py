import platform
import threading
from datetime import time


# sharex - ось х для всех субплот кривых
from Open_csv import Open_csv
from HHT import SignalProcessor
import numpy as np
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from matplotlib.figure import Figure

plt.rcParams.update({'font.size': 22, 'font.family': "Times New Roman"})
# plt.rcParams["font.family"] = "Times New Roman"
from scipy.signal import hilbert, stft
from scipy.fft import fft, fftfreq
from PyEMD import EMD
import tkinter as tk
from tkinter import filedialog, messagebox, Scrollbar, Canvas, BOTH, Y, LEFT, RIGHT, TOP, BOTTOM, X, Frame, NW, ttk
import os
import pathlib
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
import csv


class MyUI:
    def __init__(self):
        """Конструктор класса UI."""
        self.figures = []
        self.plot_names = []
        self.root = tk.Tk()
        self.csv_path = ""
        self.work_with_signal = SignalProcessor(2500, [], [])  # Initialize with a default fs
        self.root.title(" FFT + HHT")
        self.root.geometry("800x600")

        self.selected_method = tk.StringVar(value="Метод Гильберта-Хуанга")
        self.selected_type_of_pot_HHT = tk.StringVar(value="Исходный сигнал")
        self.selected_type_of_pot_FFT = tk.StringVar(value="Исходный сигнал")
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.method_vars = {
            "Метод Гильберта-Хуанга": tk.BooleanVar(),
            "Фурье метод(FFT)+ЭМД": tk.BooleanVar()
        }
        self.coords_label = None
        self.method_type_of_plots_HHT = {
            "Исходный сигнал": tk.BooleanVar(),
            "Моды сигнала (ЭДМ)": tk.BooleanVar(),
            "Мгновенные амплитуды и частоты мод (HHT)": tk.BooleanVar(),
            "Маргинальный спектр (HHT)": tk.BooleanVar()
        }

        self.method_type_of_plots_FFT = {
            "Исходный сигнал": tk.BooleanVar(),
            "Моды сигнала (ЭДМ)": tk.BooleanVar(),
            "FFT спектр": tk.BooleanVar(),
            "STFT спектр": tk.BooleanVar(),
            "АЧХ спектры(FFT) + Моды сигнала (ЭДМ)": tk.BooleanVar()
        }

        self.current_selected_file = None
        self.list_frame = tk.Frame(self.root)
        self.list_frame.pack(side=LEFT, fill=BOTH, expand=False)

        self.listbox = tk.Listbox(self.list_frame, width=15)
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.listbox.bind("<ButtonRelease-1>", self.on_listbox_click)

        self.scrollbar = Scrollbar(self.list_frame, orient="vertical")
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        # Bind mouse wheel to Listbox
        # self.bind_mousewheel(self.listbox, self.listbox)

        self.content_frame = Frame(self.root)
        self.content_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        # Frame to hold the plot canvas
        self.plot_container = Frame(self.content_frame)
        self.plot_container.pack(side=TOP, fill=BOTH, expand=True)

        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_container)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=TOP, fill=BOTH, expand=True)
        self.ax = self.figure.add_subplot(111)

        self.path_to_folder = ""
        self.file_list = []
        self.file_menu_plots = None  # Initialize the file_menu_plots attribute
        self.create_menu()
        self.menu_of_math_method()
        self.create_menu_plot()
        self.menu_of_plots()

        self.update_list(["Загрузите", "папку"])





    def clear_plot(self):
        # self.figure.clear()
        # self.ax = self.figure.add_subplot(111)
        for child in self.plot_container.winfo_children():
            child.destroy()
        # self.canvas.draw()

    def plot_data(self, x_data, y_data, title, xlabel, ylabel):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.plot(x_data, y_data, color="blue")
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True)
        self.canvas.draw()

    def menu_of_math_method(self):
        """Создание меню 'Обработка сигнала'."""
        file_menu_signal = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Обработка сигнала", menu=file_menu_signal)

        for method in self.method_vars.keys():
            file_menu_signal.add_radiobutton(
                label=method,
                variable=self.selected_method,
                value=method,
                command=lambda m=method: self.select_math_method(m)
            )

    def create_menu_plot(self):
        self.file_menu_plots = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Тип кривых", menu=self.file_menu_plots)

    def menu_of_plots(self):
        """Создание меню 'Тип кривых'."""
        self.file_menu_plots.delete(0, "end")  # Clear existing items

        if self.selected_method.get() == "Метод Гильберта-Хуанга":
            for method1 in self.method_type_of_plots_HHT.keys():
                self.file_menu_plots.add_radiobutton(
                    label=method1,
                    variable=self.selected_type_of_pot_HHT,
                    value=method1,
                    command=lambda m=method1: self.select_plot_method_EMD(m)
                )
        elif self.selected_method.get() == "Фурье метод(FFT)+ЭМД":
            for method1 in self.method_type_of_plots_FFT.keys():
                self.file_menu_plots.add_radiobutton(
                    label=method1,
                    variable=self.selected_type_of_pot_FFT,
                    value=method1,
                    command=lambda m=method1: self.select_plot_method_FFT(m)
                )

    def select_math_method(self, method):
        """Устанавливает выбранный метод обработки сигнала и обновляет меню 'Тип кривых'."""
        for key in self.method_vars:
            self.method_vars[key].set(key == method)
        # self.selected_method.set(method)
        print(f"Выбран метод обработки: {method}")

        # Update the "Тип кривых" menu
        self.menu_of_plots()

        # If the method is "Фурье метод(FFT)+ЭМД", automatically set the plot type to "Исходный сигнал"
        if method == "Фурье метод(FFT)+ЭМД":
            # self.work_with_signal.perform_emd()
            self.selected_type_of_pot_FFT.set("Исходный сигнал")
            self.select_plot_method_FFT("Исходный сигнал")
        elif method == "Метод Гильберта-Хуанга":
            # self.work_with_signal.perform_emd()
            self.selected_type_of_pot_HHT.set("Исходный сигнал")
            self.select_plot_method_EMD("Исходный сигнал")

    def select_plot_method_EMD(self, method):
        x, y = self.read_csv_x_y()
        """Устанавливает выбранный метод, снимает выделение с других методов и выводит в консоль."""
        for key in self.method_type_of_plots_HHT:
            self.method_type_of_plots_HHT[key].set(key == method)
        self.selected_type_of_pot_HHT.set(method)
        print(f"Выбран тип графика: {method}")
        # Clear the plot container before drawing a new plot type
        for widget in self.plot_container.winfo_children():
            widget.destroy()
        if method == "Исходный сигнал":
            self.figure = Figure(figsize=(6, 4), dpi=100)  # Recreate the figure
            self.ax = self.figure.add_subplot(111)  # Recreate the standard axes
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_container)  # Recreate the canvas
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(side=TOP, fill=BOTH, expand=True)
            self.plot_just_signal(x, y)
        elif method == "Моды сигнала (ЭДМ)":
            self.plot_signal_mods(x, y)
        elif method == "Мгновенные амплитуды и частоты мод (HHT)":
            self.plot_instantaneous_amplitude_and_frequency()
        elif method == "Маргинальный спектр (HHT)":
            self.plot_marginal_spectrum()

    def read_csv_x_y(self):
        csv_reader = Open_csv(self.csv_path)
        csv_reader.calculcated_all_lists()
        y = csv_reader.amplitude_list
        x = csv_reader.times_list
        return x, y

    def select_plot_method_FFT(self, method):
        x, y = self.read_csv_x_y()
        """Устанавливает выбранный метод, снимает выделение с других методов и выводит в консоль."""
        for key in self.method_type_of_plots_HHT:
            self.method_type_of_plots_HHT[key].set(key == method)
        self.selected_type_of_pot_HHT.set(method)
        print(f"Выбран тип графика: {method}")
        # Clear the plot container before drawing a new plot type
        for widget in self.plot_container.winfo_children():
            widget.destroy()
        if method == "Исходный сигнал":
            self.figure = Figure(figsize=(6, 4), dpi=100)  # Recreate the figure
            self.ax = self.figure.add_subplot(111)  # Recreate the standard axes
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_container)  # Recreate the canvas
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(side=TOP, fill=BOTH, expand=True)
            self.plot_just_signal(x, y)
        elif method == "Моды сигнала (ЭДМ)":
            self.plot_signal_mods(x, y)
        elif method == "АЧХ спектры(FFT) + Моды сигнала (ЭДМ)":
            self.plot_signal_mods_afc_spectrum()
        elif method == "STFT спектр":
            self.plot_stft_spectrum()
        elif method == "FFT спектр":
            self.plot_fft_spectrum()

    def plot_just_signal(self, x_in, y_in):
        if not self.csv_path:
            print("Не выбран CSV файл для отображения.")
            return

        # csv_reader = Open_csv(self.csv_path)
        # csv_reader.calculcated_all_lists()
        y = y_in
        x = x_in

        if not x:
            print("Нет массива времени.")
            return

        self.work_with_signal.fs = int(1 / (x[1] - x[0])) if len(x) > 1 and (
                x[1] - x[0]) > 0 else 2500  # Update sampling frequency
        self.work_with_signal.t = np.array(x)
        self.work_with_signal.set_signal(y)
        self.plot_data(x, y, 'Original signal', 'Time, s', 'Amplitude, V')

    def plot_signal_mods(self, x, y):
        if not self.csv_path:
            print("Не выбран CSV файл для отображения мод сигнала.")
            return
        if not x:
            print("Отсутствуют данные времени по IMFs.")
            return
        self.work_with_signal.fs = int(1 / (x[1] - x[0])) if len(x) > 1 and (x[1] - x[0]) > 0 else 2500
        self.work_with_signal.t = np.array(x)
        self.work_with_signal.set_signal(y)
        # self.work_with_signal.perform_emd()
        if self.work_with_signal.IMFs is not None:
            num_imfs = self.work_with_signal.IMFs.shape[0]

            # чистим предыущие графики
            for widget in self.plot_container.winfo_children():
                widget.destroy()

            # создаем новую рамку
            scrollable_frame = tk.Frame(self.plot_container)
            scrollable_frame.pack(fill=tk.BOTH, expand=True)

            canvas_scrollable = tk.Canvas(scrollable_frame)
            canvas_scrollable.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            scrollbar_imf = tk.Scrollbar(scrollable_frame, orient=tk.VERTICAL, command=canvas_scrollable.yview)
            scrollbar_imf.pack(side=tk.RIGHT, fill=tk.Y)

            canvas_scrollable.configure(yscrollcommand=scrollbar_imf.set)
            canvas_scrollable.bind('<Configure>',
                                   lambda e: canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all")))

            # Comprehensive scroll handling function
            def _scroll_handler(event, canvas):
                # Handle mouse wheel scrolling
                if event.type == tk.EventType.MouseWheel:
                    # Windows and MacOS
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif event.type == tk.EventType.ButtonPress:
                    # Linux mouse wheel
                    if event.num == 4:
                        canvas.yview_scroll(-1, "units")
                    elif event.num == 5:
                        canvas.yview_scroll(1, "units")

                # Handle keyboard scrolling
                elif event.type == tk.EventType.KeyPress:
                    if event.keysym == 'Up':
                        canvas.yview_scroll(-1, "units")
                    elif event.keysym == 'Down':
                        canvas.yview_scroll(1, "units")
                    elif event.keysym == 'Prior':  # Page Up
                        canvas.yview_scroll(-1, "pages")
                    elif event.keysym == 'Next':  # Page Down
                        canvas.yview_scroll(1, "pages")

                return "break"

            # Create a list to track all widgets that need scroll binding
            scroll_widgets = []

            imf_plot_frame = tk.Frame(canvas_scrollable)
            imf_plot_frame.pack(fill=tk.BOTH, expand=True)
            canvas_scrollable.create_window((0, 0), window=imf_plot_frame, anchor=tk.NW)

            # Calculate the height of each subplot
            subplot_height = 6.5  # Adjust this value as needed
            total_height = num_imfs * subplot_height

            for i in range(num_imfs):
                imf_figure = Figure(figsize=(13, subplot_height), dpi=100)
                ax_imf = imf_figure.add_subplot(111)
                ax_imf.plot(self.work_with_signal.t, self.work_with_signal.IMFs[i], color='blue')
                ax_imf.set_title(f'$IMF_{{{i + 1}}}$')
                ax_imf.set_xlabel('Time, s')
                ax_imf.set_ylabel('Amplitude, V')
                ax_imf.grid(True)
                self.figures.append(imf_figure)
                self.plot_names.append('Мода_' + str(i + 1) + '.png')
                canvas_imf = FigureCanvasTkAgg(imf_figure, master=imf_plot_frame)
                canvas_imf_widget = canvas_imf.get_tk_widget()

                toolbar = NavigationToolbar2Tk(canvas_imf, imf_plot_frame)
                toolbar.update()
                # Pack toolbar and canvas
                toolbar.pack(side=tk.TOP, fill=tk.X)
                canvas_imf_widget.pack(fill=tk.BOTH, expand=True)
                canvas_imf.draw()

                # Add to scroll widgets
                scroll_widgets.extend([
                    canvas_scrollable,
                    scrollable_frame,
                    canvas_imf_widget,
                    imf_plot_frame
                ])
                imf_figure.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

            # Bind scroll events to all relevant widgets
            for widget in scroll_widgets:
                # Mouse wheel events (Windows and MacOS)
                widget.bind("<MouseWheel>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))

                # Linux mouse wheel events
                widget.bind("<Button-4>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
                widget.bind("<Button-5>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))

                # Keyboard events
                widget.bind("<Up>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
                widget.bind("<Down>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
                widget.bind("<Prior>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
                widget.bind("<Next>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))

            canvas_scrollable.focus_set()

            canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all"))

    def on_mouse_move(self, event):
        if event.inaxes:
            # Убедимся, что coords_label создается только один раз
            if self.coords_label is None:
                self.coords_label = tk.Label(self.content_frame, text="", bg="white", fg="blue")
                self.coords_label.place_forget()  # Скрываем метку при старте
            # Получаем координаты мыши
            x, y = event.xdata, event.ydata
            ax = event.inaxes
            x_pix, y_pix = ax.transData.transform((x, y))


            # x_pix, y_pix = ax.transData.transform((x, y))
            #
            # canvas_widget1 = self.canvas.get_tk_widget()
            # canvas_widget1.pack(side=TOP, fill=BOTH, expand=True)
            #
            # canvas_x, canvas_y = canvas_widget1.winfo_rootx(), canvas_widget1.winfo_rooty()
            # axes_x, axes_y, axes_width, axes_height = ax.bbox.bounds
            # label_x = canvas_x + axes_x + x_pix
            # label_y = canvas_y + (axes_y + axes_height) - y_pix



            # Размещаем метку относительно координат курсора
            self.coords_label.place(x=event.x , y=event.y )

            self.coords_label.config(text=f"x={x:.2e}, y={y:.2e}")
            self.coords_label.lift()
        else:
            # Скрываем метку, если мышь выходит за пределы графика
            if self.coords_label is not None:
                self.coords_label.place_forget()

    def plot_signal_mods_afc_spectrum(self):
        if not self.csv_path:
            print("Не выбран CSV файл для отображения.")
            return

        x, y = self.read_csv_x_y()

        if not x:
            print("Отсутствуют данные времени.")
            return

        self.work_with_signal.fs = int(1 / (x[1] - x[0])) if len(x) > 1 and (x[1] - x[0]) > 0 else 2500
        self.work_with_signal.t = np.array(x)
        self.work_with_signal.set_signal(y)

        if self.work_with_signal.IMFs is None:
            print("Не удалось выполнить EMD.")
            return

        # Clear existing widgets
        for widget in self.plot_container.winfo_children():
            widget.destroy()

        scrollable_frame = tk.Frame(self.plot_container)
        scrollable_frame.pack(fill=tk.BOTH, expand=True)

        canvas_scrollable = tk.Canvas(scrollable_frame)
        canvas_scrollable.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(scrollable_frame, orient=tk.VERTICAL, command=canvas_scrollable.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas_scrollable.configure(yscrollcommand=scrollbar.set)
        canvas_scrollable.bind('<Configure>',
                               lambda e: canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all")))

        def _scroll_handler(event, canvas):
            if event.type == tk.EventType.MouseWheel:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.type == tk.EventType.ButtonPress:
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
            elif event.type == tk.EventType.KeyPress:
                if event.keysym == 'Up':
                    canvas.yview_scroll(-1, "units")
                elif event.keysym == 'Down':
                    canvas.yview_scroll(1, "units")
                elif event.keysym == 'Prior':
                    canvas.yview_scroll(-1, "pages")
                elif event.keysym == 'Next':
                    canvas.yview_scroll(1, "pages")
            return "break"

        plot_frame = tk.Frame(canvas_scrollable)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        canvas_scrollable.create_window((0, 0), window=plot_frame, anchor=tk.NW)

        scroll_widgets = []

        num_imfs = self.work_with_signal.IMFs.shape[0]
        subplot_height = 5

        for i in range(num_imfs):
            imf_figure = Figure(figsize=(12, subplot_height * 2), dpi=100)
            axs = imf_figure.subplots(2, 1)  # Remove sharex=True
            imfs_i = self.work_with_signal.IMFs[i]
            xf, magnitude_spectrum = self.work_with_signal.perform_fft_in(imfs_i)

            line1 = axs[0].plot(xf, magnitude_spectrum, color='blue', picker=5)  # Add label
            axs[0].set_title(f'FFT spectrum $IMF_{{{i + 1}}}$')
            axs[0].set_xlabel('Frequency, Hz')
            axs[0].set_ylabel('Amplitude, V')
            axs[0].grid(True)

            line2 = axs[1].plot(self.work_with_signal.t, imfs_i, color='red', picker=5)  # Add label
            axs[1].set_title(f'$IMF_{{{i + 1}}}$')
            axs[1].set_xlabel('Time, s')
            axs[1].set_ylabel('Amplitude, V')
            axs[1].grid(True)
            self.figures.append(imf_figure)
            self.plot_names.append('Мода_' + str(i + 1) + '+АЧХ' + '.png')

            imf_figure.tight_layout()

            canvas_imf = FigureCanvasTkAgg(imf_figure, master=plot_frame)
            canvas_imf_widget = canvas_imf.get_tk_widget()

            toolbar_imf = NavigationToolbar2Tk(canvas_imf, plot_frame)
            toolbar_imf.update()
            toolbar_imf.pack(side=tk.TOP, fill=tk.X)
            canvas_imf_widget.pack(fill=tk.BOTH, expand=True)
            canvas_imf.draw()

            scroll_widgets.extend([
                canvas_scrollable,
                scrollable_frame,
                canvas_imf_widget,
                plot_frame
            ])

        for widget in scroll_widgets:
            # Mouse  (Windows and MacOS)
            widget.bind("<MouseWheel>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))

            # Linux
            widget.bind("<Button-4>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
            widget.bind("<Button-5>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))

            widget.bind("<Up>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
            widget.bind("<Down>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
            widget.bind("<Prior>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
            widget.bind("<Next>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))

        canvas_scrollable.focus_set()
        canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all"))

        # save_button = tk.Button(self.plot_container, text="Save All Plots",
        #                         command=lambda: self.save_all_plots(self.figures, self.plot_names))
        # save_button.pack(side=tk.BOTTOM, pady=10)
        # if(self.create_menu().entrycget(2,'label')):
        #         self.save_all_plots(self.figures, self.plot_names)
        # save_button = tk.Button(self.plot_container, text="Save All Plots",
        #                         command=lambda: self.save_all_plots(self.figures, self.plot_names))
        # save_button.pack(side=tk.BOTTOM, pady=10)

    def perform_save(self, figures, names, save_path):
        try:
            for i, (fig, filename) in enumerate(zip(figures, names)):
                fig.savefig(os.path.join(save_path, filename))
                self.progress["value"] = i + 1
                self.progress.update()
            # time.sleep(0.1)  # Симуляция задержки

            self.loading_window.destroy()
            messagebox.showinfo("Выполнено", "Все рисунки успешно сохранены в папке: " + save_path)
        except Exception as e:
            self.loading_window.destroy()
            messagebox.showerror("Ошибка", f"Ошибка сохранения рисунков: {str(e)}")

    def save_all_plots(self, figures, names):
        save_path = filedialog.askdirectory(title="Выберите папку для сохранения")
        if not save_path:
            return

        # Создаем окно загрузки
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Сохранение")
        self.loading_window.geometry("300x100")
        self.label = tk.Label(self.loading_window, text="Сохранение рисунков...")
        self.label.pack(pady=10)

        self.progress = ttk.Progressbar(self.loading_window, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(pady=10)

        self.progress["value"] = 0
        self.progress["maximum"] = len(figures)

        # Запускаем сохранение рисунков в отдельном потоке
        threading.Thread(target=self.perform_save, args=(figures, names, save_path)).start()



    def plot_instantaneous_amplitude_and_frequency(self):
        if not self.csv_path:
            print("Не выбран CSV файл для отображения амплитуды и частоты мод.")
            return

        if self.work_with_signal.IMFs is None or self.work_with_signal.num_imfs == 0:
            print("Сначала выполните ЭМД.")
            return

        self.work_with_signal.apply_hilbert_transform()
        num_imfs = self.work_with_signal.num_imfs

        # Clear existing widgets
        for widget in self.plot_container.winfo_children():
            widget.destroy()

        # Create a frame with a scrollbar
        scrollable_frame = tk.Frame(self.plot_container)
        scrollable_frame.pack(fill=tk.BOTH, expand=True)

        canvas_scrollable = tk.Canvas(scrollable_frame)
        canvas_scrollable.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(scrollable_frame, orient=tk.VERTICAL, command=canvas_scrollable.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas_scrollable.configure(yscrollcommand=scrollbar.set)
        canvas_scrollable.bind('<Configure>',
                               lambda e: canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all")))

        # Comprehensive scroll handling function
        def _scroll_handler(event, canvas):
            # Handle mouse wheel scrolling
            if event.type == tk.EventType.MouseWheel:
                # Windows and MacOS
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.type == tk.EventType.ButtonPress:
                # Linux mouse wheel
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")

            # Handle keyboard scrolling
            elif event.type == tk.EventType.KeyPress:
                if event.keysym == 'Up':
                    canvas.yview_scroll(-1, "units")
                elif event.keysym == 'Down':
                    canvas.yview_scroll(1, "units")
                elif event.keysym == 'Prior':  # Page Up
                    canvas.yview_scroll(-1, "pages")
                elif event.keysym == 'Next':  # Page Down
                    canvas.yview_scroll(1, "pages")

            return "break"

        plot_frame = tk.Frame(canvas_scrollable)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        canvas_scrollable.create_window((0, 0), window=plot_frame, anchor=tk.NW)

        # List to track widgets for scroll binding
        scroll_widgets = []

        # Calculate the height of each subplot
        subplot_height = 8  # Adjusted for two subplots per IMF

        for i in range(num_imfs):
            figure = Figure(figsize=(12, subplot_height), dpi=100)
            axs = figure.subplots(2, 1, sharex=True)

            # Plot instantaneous amplitude
            axs[0].plot(self.work_with_signal.t, self.work_with_signal.inst_amplitudes[i],
                        color='blue')
            axs[0].set_title(f'$IMF_{{{i + 1}}}$ - Instantaneous amplitude')
            axs[0].set_ylabel('Amplitude, V')
            axs[0].grid(True)

            # Plot instantaneous frequency
            axs[1].plot(self.work_with_signal.t[:-1], np.abs(self.work_with_signal.inst_frequencies[i][:-1]),
                        color='red')
            axs[1].set_title(f'$IMF_{{{i + 1}}}$ - Instantaneous frequency')
            axs[1].set_xlabel('Time, s')
            axs[1].set_ylabel('frequency, Hz')
            axs[1].grid(True)
            self.figures.append(figure)
            self.plot_names.append('Мгновенные амплитуда & частота моды ' + str(i + 1) + '.png')
            figure.tight_layout()

            # Create canvas and toolbar for each figure
            canvas = FigureCanvasTkAgg(figure, master=plot_frame)
            canvas_widget = canvas.get_tk_widget()

            toolbar = NavigationToolbar2Tk(canvas, plot_frame)
            toolbar.update()

            # Pack toolbar and canvas
            toolbar.pack(side=tk.TOP, fill=tk.X)
            canvas_widget.pack(fill=tk.BOTH, expand=True)
            canvas.draw()

            # Add to scroll widgets
            scroll_widgets.extend([
                canvas_scrollable,
                scrollable_frame,
                canvas_widget,
                plot_frame
            ])

        # Bind scroll events to all relevant widgets
        for widget in scroll_widgets:
            # Mouse wheel events (Windows and MacOS)
            widget.bind("<MouseWheel>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))

            # Linux mouse wheel events
            widget.bind("<Button-4>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
            widget.bind("<Button-5>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))

            # Keyboard events
            widget.bind("<Up>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
            widget.bind("<Down>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
            widget.bind("<Prior>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))
            widget.bind("<Next>", lambda e, c=canvas_scrollable: _scroll_handler(e, c))

        # Make canvas focusable to receive keyboard events
        canvas_scrollable.focus_set()

        # Update the canvas scroll region
        canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all"))

    def plot_marginal_spectrum(self):
        # self.work_with_signal.perform_emd()
        self.work_with_signal.apply_hilbert_transform()
        if not self.csv_path:
            print("Не выбран CSV файл для отображения маргинального спектра.")
            return

        if not self.work_with_signal.inst_frequencies or not self.work_with_signal.inst_amplitudes:
            print("Сначала выполните преобразование Гильберта.")
            return

        self.work_with_signal.compute_marginal_spectrum()
        if self.work_with_signal.marginal_spectrum is None:
            print("Ошибка при вычислении маргинального спектра.")
            return

        # Clear any existing content in the plot container
        for widget in self.plot_container.winfo_children():
            widget.destroy()

        # Create a frame with a scrollbar
        scrollable_frame = tk.Frame(self.plot_container)
        scrollable_frame.pack(fill=tk.BOTH, expand=True)

        canvas_scrollable = tk.Canvas(scrollable_frame)
        canvas_scrollable.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(scrollable_frame, orient=tk.VERTICAL, command=canvas_scrollable.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas_scrollable.configure(yscrollcommand=scrollbar.set)
        canvas_scrollable.bind('<Configure>',
                               lambda e: canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all")))

        plot_frame = tk.Frame(canvas_scrollable)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        canvas_scrollable.create_window((0, 0), window=plot_frame, anchor=tk.NW)

        # Create figure for marginal spectrum
        figure = Figure(figsize=(13, 6.2), dpi=100)
        ax = figure.add_subplot(111)

        # Calculate frequency bins and plot
        freq_bins = np.linspace(0, self.work_with_signal.fs / 2, self.work_with_signal.fs // 2 + 1)
        ax.plot(freq_bins, self.work_with_signal.marginal_spectrum, color='blue')

        # Set titles and labels
        ax.set_title('Marginal signal spectrum')
        ax.set_xlabel('Frequency, Hz')
        ax.set_ylabel('Normalized amplitude')
        ax.grid(True)

        # Create canvas and toolbar
        canvas = FigureCanvasTkAgg(figure, master=plot_frame)
        canvas_widget = canvas.get_tk_widget()

        toolbar = NavigationToolbar2Tk(canvas, plot_frame)
        toolbar.update()

        # Pack toolbar and canvas
        toolbar.pack(side=tk.TOP, fill=tk.X)
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas.draw()

        # Update the canvas scroll region
        canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all"))

    def plot_stft_spectrum(self):
        if not self.csv_path:
            print("Не выбран CSV файл для отображения STFT.")
            return

        # Perform STFT
        f, t_stft, Zxx = self.work_with_signal.perform_stft()
        if f is None or t_stft is None or Zxx is None:
            print("Ошибка при выполнении STFT.")
            return

        # Clear any existing content in the plot container
        for widget in self.plot_container.winfo_children():
            widget.destroy()

        # Create a frame with a scrollbar
        scrollable_frame = tk.Frame(self.plot_container)
        scrollable_frame.pack(fill=tk.BOTH, expand=True)

        canvas_scrollable = tk.Canvas(scrollable_frame)
        canvas_scrollable.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(scrollable_frame, orient=tk.VERTICAL, command=canvas_scrollable.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas_scrollable.configure(yscrollcommand=scrollbar.set)
        canvas_scrollable.bind('<Configure>',
                               lambda e: canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all")))

        plot_frame = tk.Frame(canvas_scrollable)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        canvas_scrollable.create_window((0, 0), window=plot_frame, anchor=tk.NW)

        # Create figure for STFT spectrum
        figure = Figure(figsize=(12, 6), dpi=100)
        ax = figure.add_subplot(111)

        # Plot STFT
        mesh = ax.pcolormesh(t_stft, f, np.abs(Zxx), shading='gouraud', cmap='viridis', color='blue')

        # Set titles and labels
        ax.set_title('STFT Magnitude')
        ax.set_ylabel('Frequency, Hz')
        ax.set_xlabel('Time, s')

        # Add colorbar
        colorbar = figure.colorbar(mesh, ax=ax, label='Magnitude')

        # Set frequency limit
        ax.set_ylim(0, self.work_with_signal.fs / 2)

        # Adjust layout to prevent colorbar cutoff
        figure.tight_layout()
        ax.set_yscale('linear')
        # Create canvas and toolbar
        canvas = FigureCanvasTkAgg(figure, master=plot_frame)
        canvas_widget = canvas.get_tk_widget()

        toolbar = NavigationToolbar2Tk(canvas, plot_frame)
        toolbar.update()

        # Pack toolbar and canvas
        toolbar.pack(side=tk.TOP, fill=tk.X)
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas.draw()

        # Update the canvas scroll region
        canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all"))

    def plot_fft_spectrum(self):
        if not self.csv_path:
            print("Не выбран CSV файл для отображения FFT.")
            return

        # Perform FFT
        xf, magnitude_spectrum = self.work_with_signal.perform_fft()
        if xf is None or magnitude_spectrum is None:
            print("Ошибка при выполнении FFT.")
            return

        # Clear any existing content in the plot container
        for widget in self.plot_container.winfo_children():
            widget.destroy()

        # Create a frame with a scrollbar
        scrollable_frame = tk.Frame(self.plot_container)
        scrollable_frame.pack(fill=tk.BOTH, expand=True)

        canvas_scrollable = tk.Canvas(scrollable_frame)
        canvas_scrollable.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(scrollable_frame, orient=tk.VERTICAL, command=canvas_scrollable.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas_scrollable.configure(yscrollcommand=scrollbar.set)
        canvas_scrollable.bind('<Configure>',
                               lambda e: canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all")))

        plot_frame = tk.Frame(canvas_scrollable)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        canvas_scrollable.create_window((0, 0), window=plot_frame, anchor=tk.NW)

        # Create figure for FFT spectrum
        figure = Figure(figsize=(12, 6), dpi=100)
        ax = figure.add_subplot(111)
        # Plot FFT spectrum (only first half due to symmetry)
        ax.plot(xf[:len(xf) // 2], magnitude_spectrum[:len(magnitude_spectrum) // 2], color='blue')

        # Set titles and labels
        ax.set_title('AFC (FFT)')
        ax.set_xlabel('Frequency, Hz')
        ax.set_ylabel('Amplitude, V')
        ax.grid(True)

        # Add logarithmic scale option for better visualization
        ax.set_yscale('log')

        # Adjust layout
        figure.tight_layout()
        ax.set_yscale('linear')
        # Create canvas and toolbar
        canvas = FigureCanvasTkAgg(figure, master=plot_frame)
        canvas_widget = canvas.get_tk_widget()

        toolbar = NavigationToolbar2Tk(canvas, plot_frame)
        toolbar.update()

        # Pack toolbar and canvas
        toolbar.pack(side=tk.TOP, fill=tk.X)
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas.draw()

        # Update the canvas scroll region
        canvas_scrollable.configure(scrollregion=canvas_scrollable.bbox("all"))

        # Optional: Add buttons for switching between linear and log scale
        scale_frame = tk.Frame(plot_frame)
        scale_frame.pack(side=tk.TOP, fill=tk.X)

        def set_linear_scale():
            ax.set_yscale('linear')
            canvas.draw()

        def set_log_scale():
            ax.set_yscale('log')
            canvas.draw()

        tk.Button(scale_frame, text="Линейная шкала по y", command=set_linear_scale).pack(side=tk.LEFT, padx=5)
        tk.Button(scale_frame, text="Log шкала по y", command=set_log_scale).pack(side=tk.LEFT, padx=5)

    def loop(self):
        self.root.mainloop()

    def on_listbox_click(self, event):
        """
        Обработчик события щелчка по элементу Listbox.
        Устанавливает метод обработки сигнала "Метод Гильберта-Хуанга" и тип кривых "Исходный сигнал".
        """
        try:
            index = self.listbox.curselection()[0]
            value = self.listbox.get(index)
            print(f"Выбран элемент: {value} (индекс: {index})")
            original_path = pathlib.Path(os.path.join(self.path_to_folder, value))
            converted_path = str(original_path)  # Convert to string
            self.csv_path = converted_path
            x, y = self.read_csv_x_y()
            self.plot_just_signal(x, y)
            self.work_with_signal.perform_emd()
            print(converted_path)

            # Установка метода обработки сигнала "Метод Гильберта-Хуанга"
            self.selected_method.set("Метод Гильберта-Хуанга")
            self.select_math_method("Метод Гильберта-Хуанга")

            # Установка типа кривых "Исходный сигнал"
            self.selected_type_of_pot_HHT.set("Исходный сигнал")
            self.select_plot_method_EMD("Исходный сигнал")

            return converted_path
        except IndexError:
            print("Ошибка: элемент не выбран.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    def open_folder(self):
        """Функция для открытия папки с файлами CSV."""
        folder_path = filedialog.askdirectory(title="Выберите папку")
        if folder_path:
            try:
                file_paths = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if
                              file.endswith('.csv') or file.endswith('.CSV')]
                if file_paths:
                    name_of_files = []
                    self.path_to_folder = folder_path
                    print(self.path_to_folder)
                    for file_path in file_paths:
                        name_of_files.append(os.path.basename(file_path))
                    self.update_list(name_of_files)
                else:
                    messagebox.showinfo("Нет CSV файлов", "В выбранной папке нет файлов с расширением .csv")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{e}")
        else:
            messagebox.showinfo("Отмена", "Открытие папки отменено")

    def exit_app(self):
        """Функция для выхода из приложения."""
        self.root.destroy()

    def create_menu(self):
        """Создание меню 'Файл'."""
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть папку", command=lambda: self.open_folder())
        file_menu.add_separator()
        file_menu.add_command(label="Сохранить рисунки",
                              command=lambda: self.save_all_plots(self.figures, self.plot_names))
        file_menu.add_separator()
        file_menu.add_command(label="Очисть график", command=lambda: self.clear_plot())
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.exit_app)
        return file_menu

    def update_list(self, items):

        """Обновляет список элементов."""
        self.listbox.delete(0, tk.END)  # Очищаем список
        for item in items:
            self.listbox.insert(tk.END, item)


if __name__ == "__main__":
    ui = MyUI()
    ui.loop()
