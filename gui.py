import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
import os
import subprocess

class PVWindSimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Energieanlagen-Simulator")

        self.pv_systems = []
        self.wind_systems = []

        self.editing_index_pv = None
        self.editing_index_wind = None

        # Mapping GUI-Feld -> interne Datenstruktur (PV)
        self.PV_GUI_TO_DATA = {
            "Name": "name",
            "Nennleistung (MW)": "rated_power",
            "Alter": "age",
            "Beschattung (0-1)": "shading",
            "Albedo (0-1)": "albedo",
            "Azimut (°)": "azimut",
            "Verschmutzung (0-1)": "D_soil",
            "Neigung (°)": "tilt",
            "Fläche (m^2)": "size",
            "Lat": "lat",
            "Lon": "lon",
            "Datum (JJJJ-MM-DD)": "date",
        }

        # Mapping GUI-Feld -> interne Datenstruktur (Wind)
        self.WIND_GUI_TO_DATA = {
            "Name": "name",
            "Nennleistung (MW)": "rated_power",
            "Rotorradius (m)": "rotor_radius",
            "Nabenhöhe (m)": "hub_height",
            "Cut-In (m/s)": "cut_in",
            "Opt (m/s)": "rated_speed",
            "Cut-Out (m/s)": "cut_out",
            "Alpha (0-1)": "alpha",
            "Parkeffekt (0-1)": "wake_loss",
            "Lat": "lat",
            "Lon": "lon",
            "Datum (JJJJ-MM-DD)": "date",
            "Anzahl Turbinen": "turbines",
        }

        self.setup_ui()

    def setup_ui(self):
        tab_control = ttk.Notebook(self.root)
        self.pv_tab = ttk.Frame(tab_control)
        self.wind_tab = ttk.Frame(tab_control)
        tab_control.add(self.pv_tab, text="PV-Anlagen")
        tab_control.add(self.wind_tab, text="Windanlagen")
        tab_control.pack(expand=1, fill="both")

        self.create_pv_tab()
        self.create_wind_tab()

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Konfiguration speichern", command=self.save_config).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Konfiguration laden", command=self.load_config).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Simulation starten", command=self.run_simulation).pack(side="left", padx=5)

    def create_pv_tab(self):
        frame = self.pv_tab
        fields = list(self.PV_GUI_TO_DATA.keys())
        self.pv_entries = {}
        for field in fields:
            row = ttk.Frame(frame)
            row.pack(fill="x", padx=5, pady=2)
            ttk.Label(row, text=field, width=15).pack(side="left")
            entry = ttk.Entry(row)
            entry.pack(side="left", fill="x", expand=True)
            self.pv_entries[field] = entry

        ttk.Button(frame, text="Anlage hinzufügen", command=self.add_pv_system).pack(pady=5)
        self.pv_listbox = tk.Listbox(frame, height=6)
        self.pv_listbox.pack(fill="both", padx=5, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Bearbeiten", command=self.edit_pv_system).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Aktualisieren", command=self.update_pv_system).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Löschen", command=self.delete_pv_system).pack(side="left", padx=5)

    def create_wind_tab(self):
        frame = self.wind_tab
        fields = list(self.WIND_GUI_TO_DATA.keys())
        self.wind_entries = {}
        for field in fields:
            row = ttk.Frame(frame)
            row.pack(fill="x", padx=5, pady=2)
            ttk.Label(row, text=field, width=15).pack(side="left")
            entry = ttk.Entry(row)
            entry.pack(side="left", fill="x", expand=True)
            self.wind_entries[field] = entry

        ttk.Button(frame, text="Anlage hinzufügen", command=self.add_wind_system).pack(pady=5)
        self.wind_listbox = tk.Listbox(frame, height=6)
        self.wind_listbox.pack(fill="both", padx=5, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Bearbeiten", command=self.edit_wind_system).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Aktualisieren", command=self.update_wind_system).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Löschen", command=self.delete_wind_system).pack(side="left", padx=5)

    def add_pv_system(self):
        try:
            system = {
                "name": self.pv_entries["Name"].get(),
                "rated_power": float(self.pv_entries["Nennleistung (MW)"].get()),
                "age": int(self.pv_entries["Alter"].get()),
                "shading": float(self.pv_entries["Beschattung (0-1)"].get()),
                "albedo": float(self.pv_entries["Albedo (0-1)"].get()),
                "azimut": int(self.pv_entries["Azimut (°)"].get()),
                "D_soil": float(self.pv_entries["Verschmutzung (0-1)"].get()),
                "tilt": int(self.pv_entries["Neigung (°)"].get()),
                "size": float(self.pv_entries["Fläche (m^2)"].get()),
                "location": {
                    "lat": float(self.pv_entries["Lat"].get()),
                    "lon": float(self.pv_entries["Lon"].get()),
                },
                "date": self.pv_entries["Datum (JJJJ-MM-DD)"].get(),
            }
            self.pv_systems.append(system)
            self.refresh_lists()
            self.clear_pv_form()
        except Exception as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {e}")

    def add_wind_system(self):
        try:
            system = {
                "name": self.wind_entries["Name"].get(),
                "rated_power": float(self.wind_entries["Nennleistung (MW)"].get()),
                "rotor_radius": float(self.wind_entries["Rotorradius (m)"].get()),
                "hub_height": float(self.wind_entries["Nabenhöhe (m)"].get()),
                "cut_in": float(self.wind_entries["Cut-In (m/s)"].get()),
                "rated_speed": float(self.wind_entries["Opt (m/s)"].get()),
                "cut_out": float(self.wind_entries["Cut-Out (m/s)"].get()),
                "alpha": float(self.wind_entries["Alpha (0-1)"].get()),
                "wake_loss": float(self.wind_entries["Parkeffekt (0-1)"].get()),
                "location": {
                    "lat": float(self.wind_entries["Lat"].get()),
                    "lon": float(self.wind_entries["Lon"].get()),
                },
                "date": self.wind_entries["Datum (JJJJ-MM-DD)"].get(),
                "turbines": int(self.wind_entries["Anzahl Turbinen"].get()),
            }
            self.wind_systems.append(system)
            self.refresh_lists()
            self.clear_wind_form()
        except Exception as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {e}")

    def edit_pv_system(self):
        sel = self.pv_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        system = self.pv_systems[index]
        self.editing_index_pv = index

        for gui_key, entry in self.pv_entries.items():
            data_key = self.PV_GUI_TO_DATA[gui_key]
            entry.delete(0, tk.END)
            if data_key in ["lat", "lon"]:
                entry.insert(0, str(system["location"][data_key]))
            else:
                entry.insert(0, str(system.get(data_key, "")))

    def update_pv_system(self):
        if self.editing_index_pv is None:
            return
        try:
            system = {
                "name": self.pv_entries["Name"].get(),
                "rated_power": float(self.pv_entries["Nennleistung (MW)"].get()),
                "age": int(self.pv_entries["Alter"].get()),
                "shading": float(self.pv_entries["Beschattung (0-1)"].get()),
                "albedo": float(self.pv_entries["Albedo (0-1)"].get()),
                "azimut": int(self.pv_entries["Azimut (°)"].get()),
                "D_soil": float(self.pv_entries["Verschmutzung (0-1)"].get()),
                "tilt": int(self.pv_entries["Neigung (°)"].get()),
                "size": float(self.pv_entries["Fläche (m^2)"].get()),
                "location": {
                    "lat": float(self.pv_entries["Lat"].get()),
                    "lon": float(self.pv_entries["Lon"].get()),
                },
                "date": self.pv_entries["Datum (JJJJ-MM-DD)"].get(),
            }
            self.pv_systems[self.editing_index_pv] = system
            self.refresh_lists()
            self.clear_pv_form()
            self.editing_index_pv = None
        except Exception as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {e}")

    def delete_pv_system(self):
        sel = self.pv_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        del self.pv_systems[index]
        self.refresh_lists()

    def edit_wind_system(self):
        sel = self.wind_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        system = self.wind_systems[index]
        self.editing_index_wind = index

        for gui_key, entry in self.wind_entries.items():
            data_key = self.WIND_GUI_TO_DATA[gui_key]
            entry.delete(0, tk.END)
            if data_key in ["lat", "lon"]:
                entry.insert(0, str(system["location"][data_key]))
            else:
                entry.insert(0, str(system.get(data_key, "")))

    def update_wind_system(self):
        if self.editing_index_wind is None:
            return
        try:
            system = {
                "name": self.wind_entries["Name"].get(),
                "rated_power": float(self.wind_entries["Nennleistung (MW)"].get()),
                "rotor_radius": float(self.wind_entries["Rotorradius (m)"].get()),
                "hub_height": float(self.wind_entries["Nabenhöhe (m)"].get()),
                "cut_in": float(self.wind_entries["Cut-In (m/s)"].get()),
                "rated_speed": float(self.wind_entries["Opt (m/s)"].get()),
                "cut_out": float(self.wind_entries["Cut-Out (m/s)"].get()),
                "alpha": float(self.wind_entries["Alpha (0-1)"].get()),
                "wake_loss": float(self.wind_entries["Parkeffekt (0-1)"].get()),
                "location": {
                    "lat": float(self.wind_entries["Lat"].get()),
                    "lon": float(self.wind_entries["Lon"].get()),
                },
                "date": self.wind_entries["Datum (JJJJ-MM-DD)"].get(),
                "turbines": int(self.wind_entries["Anzahl Turbinen"].get()),
            }
            self.wind_systems[self.editing_index_wind] = system
            self.refresh_lists()
            self.clear_wind_form()
            self.editing_index_wind = None
        except Exception as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {e}")

    def delete_wind_system(self):
        sel = self.wind_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        del self.wind_systems[index]
        self.refresh_lists()

    def clear_pv_form(self):
        for entry in self.pv_entries.values():
            entry.delete(0, tk.END)

    def clear_wind_form(self):
        for entry in self.wind_entries.values():
            entry.delete(0, tk.END)

    def refresh_lists(self):
        self.pv_listbox.delete(0, tk.END)
        for system in self.pv_systems:
            self.pv_listbox.insert(tk.END, system["name"])

        self.wind_listbox.delete(0, tk.END)
        for system in self.wind_systems:
            self.wind_listbox.insert(tk.END, system["name"])

    def save_config(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".yaml")
        if not file_path:
            return
        config = {
            "pv_systems": self.pv_systems,
            "wind_systems": self.wind_systems,
        }
        with open(file_path, "w") as f:
            yaml.dump(config, f)
        messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")

    def load_config(self):
        file_path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
        if not file_path:
            return
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
        self.pv_systems = config.get("pv_systems", [])
        self.wind_systems = config.get("wind_systems", [])
        self.refresh_lists()

    def run_simulation(self):
        output_path = filedialog.asksaveasfilename(defaultextension=".csv", title="Ergebnis CSV speichern unter...")
        if not output_path:
            return
        with open("config.yaml", "w") as f:
            yaml.dump({
                "pv_systems": self.pv_systems,
                "wind_systems": self.wind_systems,
            }, f)
        try:
            subprocess.run(["python", "main.py", "config.yaml", output_path], check=True)
            messagebox.showinfo("Fertig", "Simulation abgeschlossen.")
        except subprocess.CalledProcessError:
            messagebox.showerror("Fehler", "Fehler bei der Ausführung von main.py")

if __name__ == "__main__":
    root = tk.Tk()
    app = PVWindSimApp(root)
    root.mainloop()