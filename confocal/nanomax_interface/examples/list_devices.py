import pylablib as pll

comm_type = ["serial", "visa"]

if __name__ == "__main__":
    print("Listing serial and visa devices.")
    print("NOTE: same device can appear twice (in visa and serial list)")
    print("NOTE: IP devices can't be listed with this soft")

    for comm in comm_type:
        print(comm + ':')
        print(pll.list_backend_resources(comm))
