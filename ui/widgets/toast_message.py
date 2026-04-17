from ui.common_imports import *


# ---------------- Tiện ích ----------------
def show_message(self, msg, duration=2500, color="#4CAF50"):
        # """Hiển thị thông báo (toast) ở dưới, giữ duration ms rồi fade out."""
    if not hasattr(self, "info_label"):
        print(f"[DEBUG] show_message: info_label chưa được tạo. Nội dung: {msg}")
        return

    self.info_label.setText(msg)
    self.info_label.setStyleSheet(f"background-color:{color};color:white;padding:8px 16px;border-radius:8px;font-weight:bold;")
    self.info_label.adjustSize()
    x = (self.width() - self.info_label.width()) // 2
    y = self.height() - self.info_label.height() - 20
    self.info_label.move(x, y)
    self.info_label.show()
    effect = QGraphicsOpacityEffect(self.info_label)
    self.info_label.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", self)
    anim.setDuration(1000)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    QTimer.singleShot(duration, anim.start)
    anim.finished.connect(lambda: self.info_label.hide())
