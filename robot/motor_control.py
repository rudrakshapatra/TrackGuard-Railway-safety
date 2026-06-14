"""L298N dual motor controller for caterpillar drive"""
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False

class MotorController:
    def __init__(self, left_pins=(2,3,6), right_pins=(4,5,7)):
        self.L_IN1, self.L_IN2, self.L_EN = left_pins
        self.R_IN1, self.R_IN2, self.R_EN = right_pins
        self.speed = 0
        if HAS_GPIO:
            for p in [*left_pins, *right_pins]:
                GPIO.setup(p, GPIO.OUT)
            self.pwm_l = GPIO.PWM(self.L_EN, 1000)
            self.pwm_r = GPIO.PWM(self.R_EN, 1000)
            self.pwm_l.start(0); self.pwm_r.start(0)

    def set_speed(self, speed):
        self.speed = max(0, min(255, speed))
        pct = self.speed / 255 * 100
        if HAS_GPIO:
            self.pwm_l.ChangeDutyCycle(pct)
            self.pwm_r.ChangeDutyCycle(pct)

    def forward(self):
        if HAS_GPIO:
            GPIO.output(self.L_IN1, True);  GPIO.output(self.L_IN2, False)
            GPIO.output(self.R_IN1, True);  GPIO.output(self.R_IN2, False)
        else: print(f"[SIM] Motors FORWARD speed={self.speed}")

    def stop(self):
        if HAS_GPIO:
            for p in [self.L_IN1, self.L_IN2, self.R_IN1, self.R_IN2]:
                GPIO.output(p, False)
        else: print("[SIM] Motors STOP")

    def cleanup(self):
        if HAS_GPIO: GPIO.cleanup()
