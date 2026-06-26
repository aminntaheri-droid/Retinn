
# RetinaPrinter v2.0
# pip install pillow reportlab pywin32
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps, ImageEnhance, ImageTk, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

CM = 300 / 2.54  # 300 DPI
LEFT = RIGHT = TOP = 1.5 * CM
BOTTOM = 2.0 * CM
GAP = 1.5 * CM
A4_W, A4_H = 3508, 2480

BRIGHTNESS = {
    'Auto (+20%)': 1.20,
    '+30%': 1.30,
    '+40%': 1.40,
}

class App:
    def __init__(self, root):
        self.root = root
        root.title('Retina Printer v2.0')
        root.geometry('620x260')

        tk.Label(root, text='تاریخ:').grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.date = tk.Entry(root, width=20)
        self.date.grid(row=0, column=1, sticky='w')

        tk.Label(root, text='پوشه بیماران:').grid(row=1, column=0, padx=10, sticky='w')
        self.path = tk.Entry(root, width=50)
        self.path.grid(row=1, column=1)
        tk.Button(root, text='انتخاب', command=self.pick).grid(row=1, column=2)

        self.mode = ttk.Combobox(root, values=list(BRIGHTNESS.keys()), state='readonly')
        self.mode.current(0)
        self.mode.grid(row=2, column=1, sticky='w', pady=10)

        self.do_print = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text='چاپ مستقیم', variable=self.do_print).grid(row=3, column=1, sticky='w')

        tk.Button(root, text='ساخت و چاپ همه', command=self.run, font=('Tahoma', 12)).grid(row=4, column=1, pady=25)

    def pick(self):
        p = filedialog.askdirectory()
        if p:
            self.path.delete(0, 'end')
            self.path.insert(0, p)

    def enhance(self, fn):
        img = Image.open(fn).convert('RGB')
        img = ImageOps.autocontrast(img)
        img = ImageEnhance.Brightness(img).enhance(BRIGHTNESS[self.mode.get()])
        return img

    def make_page(self, folder):
        files = [os.path.join(folder, f'{i}.jpg') for i in range(1, 5)]
        for f in files:
            if not os.path.exists(f):
                raise FileNotFoundError(os.path.basename(f))

        page = Image.new('RGB', (A4_W, A4_H), 'white')
        draw = ImageDraw.Draw(page)

        usable_w = A4_W - LEFT - RIGHT - GAP
        usable_h = A4_H - TOP - BOTTOM - GAP
        cell_w = usable_w / 2
        cell_h = usable_h / 2

        positions = [
            (LEFT, TOP),
            (LEFT + cell_w + GAP, TOP),
            (LEFT, TOP + cell_h + GAP),
            (LEFT + cell_w + GAP, TOP + cell_h + GAP)
        ]

        for fn, pos in zip(files, positions):
            img = self.enhance(fn)
            img.thumbnail((int(cell_w), int(cell_h)))
            x = int(pos[0] + (cell_w - img.width) / 2)
            y = int(pos[1] + (cell_h - img.height) / 2)
            page.paste(img, (x, y))

        name = os.path.basename(folder)
        date = self.date.get()
        ytxt = int(A4_H - BOTTOM / 2)
        draw.text((int(LEFT), ytxt), name, fill='black')
        bb = draw.textbbox((0,0), date)
        draw.text((A4_W - int(RIGHT) - (bb[2]-bb[0]), ytxt), date, fill='black')
        return page

    def preview(self, img):
        w = tk.Toplevel(self.root)
        s = img.copy()
        s.thumbnail((900, 600))
        ph = ImageTk.PhotoImage(s)
        lbl = tk.Label(w, image=ph)
        lbl.image = ph
        lbl.pack()
        ok = {'v': False}
        tk.Button(w, text='تأیید و ادامه', command=lambda: (ok.__setitem__('v', True), w.destroy())).pack()
        w.grab_set(); w.wait_window()
        return ok['v']

    def pdf(self, img, out_file):
        tmp = out_file + '.jpg'
        img.save(tmp, quality=95)
        c = canvas.Canvas(out_file, pagesize=landscape(A4))
        pw, ph = landscape(A4)
        c.drawImage(tmp, 0, 0, pw, ph)
        c.save()
        os.remove(tmp)

    def run(self):
        base = self.path.get()
        if not os.path.isdir(base):
            return messagebox.showerror('خطا', 'پوشه معتبر نیست')

        out = os.path.join(base, 'Output')
        os.makedirs(out, exist_ok=True)
        report = []
        first = True

        folders = sorted([os.path.join(base, x) for x in os.listdir(base)
                          if os.path.isdir(os.path.join(base, x)) and x != 'Output'])

        for folder in folders:
            patient = os.path.basename(folder)
            try:
                page = self.make_page(folder)
                if first:
                    if not self.preview(page):
                        return
                    first = False
                pdf_name = os.path.join(out, patient + '.pdf')
                self.pdf(page, pdf_name)
                if self.do_print.get():
                    try:
                        os.startfile(pdf_name, 'print')
                    except:
                        pass
                report.append(f'[OK] {patient}')
            except Exception as e:
                report.append(f'[ERROR] {patient}: {e}')

        with open(os.path.join(out, 'Errors.txt'), 'w', encoding='utf-8') as f:
            f.write('
'.join(report))

        messagebox.showinfo('پایان', 'همه بیماران پردازش شدند.')

root = tk.Tk()
App(root)
root.mainloop()
