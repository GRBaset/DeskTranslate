import time

import cv2
import numpy as np
import pytesseract
import pyttsx3
from PIL import ImageGrab
from PyQt6 import QtWidgets, QtCore, QtGui
from deep_translator import (GoogleTranslator,
                             PonsTranslator,
                             MyMemoryTranslator,
                             LingueeTranslator,
                             LibreTranslator)

#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class Worker(QtCore.QObject):
    def __init__(self, snip_window, image_lang_code, trans_lang_code, is_text2speech_enabled, ui, translator_engine,
                 libre_url, libre_api, img_lang, trans_lang):
        super().__init__()
        img = ImageGrab.grab()
        logical_width = snip_window.rect.width()
        physical_width = img.getdata().size[0]
        pixel_ratio = physical_width / logical_width

        self.x1 = min(snip_window.begin.x(), snip_window.end.x()) * pixel_ratio
        self.y1 = min(snip_window.begin.y(), snip_window.end.y()) * pixel_ratio
        self.x2 = max(snip_window.begin.x(), snip_window.end.x()) * pixel_ratio
        self.y2 = max(snip_window.begin.y(), snip_window.end.y()) * pixel_ratio
        self.image_lang_code = image_lang_code
        self.trans_lang_code = trans_lang_code
        self.is_text2speech_enabled = is_text2speech_enabled
        self.ui = ui
        self.running = True
        self.translator_engine = translator_engine
        self.current_extracted_text = None
        self.img_lang = img_lang.lower()
        self.trans_lang = trans_lang.lower()
        self.libre_url = libre_url
        self.libre_api = libre_api

    def stop_running(self):
        self.running = False

    def run(self):
        while self.running:
            img = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2))
            img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)

            new_extracted_text = pytesseract.image_to_string(img, lang=self.image_lang_code).strip()
            new_extracted_text = " ".join(new_extracted_text.split())
            print(f"EXTRACTED TEXT: [{new_extracted_text}]")

            if len(new_extracted_text) < 1 or len(new_extracted_text) > 4999:
                continue

            if self.current_extracted_text != new_extracted_text and new_extracted_text:
                print(f"Translating: [{new_extracted_text}] of len[{len(new_extracted_text)}]")
                self.current_extracted_text = new_extracted_text

                translated_text = ""
                print(self.img_lang, self.trans_lang)
                if self.translator_engine == "GoogleTranslator":
                    try:
                        translated_text = GoogleTranslator(source='auto', target=self.trans_lang_code).translate(
                            new_extracted_text)
                        print(f"TRANSLATED TEXT: [{translated_text}]")
                    except Exception:
                        print("unsupported by GoogleTranslate")
                elif self.translator_engine == "PonsTranslator":
                    try:
                        translated_text = PonsTranslator(source=self.img_lang, target=self.trans_lang).translate(
                            new_extracted_text)
                        print(f"TRANSLATED TEXT: [{translated_text}]")
                    except Exception:
                        print("unsupported by PonsTranslator")
                elif self.translator_engine == "LingueeTranslator":
                    try:
                        translated_text = LingueeTranslator(source=self.img_lang, target=self.trans_lang).translate(
                            new_extracted_text)
                        print(f"TRANSLATED TEXT: [{translated_text}]")
                    except Exception:
                        print("unsupported by LingueeTranslator")
                elif self.translator_engine == "MyMemoryTranslator":
                    try:
                        translated_text = MyMemoryTranslator(source=self.img_lang, target=self.trans_lang).translate(
                            new_extracted_text)
                        print(f"TRANSLATED TEXT: [{translated_text}]")
                    except Exception:
                        print("unsupported by MyMemoryTranslator")
                elif self.translator_engine == "LibreTranslator":
                    try:
                        translated_text = LibreTranslator(source="auto", target=self.trans_lang_code, custom_url=self.libre_url, api_key=self.libre_api).translate(
                            new_extracted_text)
                        print(f"TRANSLATED TEXT: [{translated_text}]")
                    except Exception:
                        print("unsupported by LibreTranslator")
                else:
                    raise Exception("unsupported translation engine")

                self.ui.translated_text_label.setText(translated_text)
                if self.is_text2speech_enabled:
                    engine = pyttsx3.init()
                    engine.say(translated_text)
                    engine.runAndWait()

            time.sleep(1)


class MyWidget(QtWidgets.QWidget): 
    def __init__(self):
        super().__init__()
        screen = QtWidgets.QApplication.primaryScreen()
        self.rect = screen.availableGeometry()
        screen_width = self.rect.width()
        screen_height = self.rect.height()
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setWindowTitle(' ')
        self.begin = QtCore.QPointF() 
        self.end = QtCore.QPointF()
        self.setWindowOpacity(0.3)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor('black'), 3))
        qp.setBrush(QtGui.QColor(128, 128, 255, 128))
        qp.setOpacity(0.5)
        qp.drawRect(self.rect)
        qp.setOpacity(1.0)
        qp.drawRect(QtCore.QRectF(self.begin, self.end))

    def mousePressEvent(self, event):
        self.begin = event.globalPosition()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.globalPosition()
        self.update()

    def mouseReleaseEvent(self, event):
        self.close()

    def closeEvent(self, event):
        QtWidgets.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor)
        )


if __name__ == '__main__':
    app = QtWidgets.QApplication([""])
    window = MyWidget()
    QtWidgets.QApplication.setOverrideCursor(
        QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor)
    )
    window.show()
    app.aboutToQuit.connect(app.deleteLater)
    app.exec_()
