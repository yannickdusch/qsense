from pylablib.devices import Thorlabs

with Thorlabs.KinesisMotor("27000000") as stage:
    stage.move_by(10000)
    stage.wait_move()

