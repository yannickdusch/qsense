from pylablib.devices import Thorlabs
import sys



def main():
    if len(sys.argv) == 1:
        print("One argument needed, returning")
        return
    
    with Thorlabs.KinesisPiezoMotor(sys.argv[1]) as stage:
        print(stage.get_drive_parameter())
        print(stage.get_full_info())


if __name__ == "__main__":
    main()
