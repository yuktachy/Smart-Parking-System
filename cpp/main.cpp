#include "classes.h"

int main() {
    ParkingManager manager;
    int choice;

    while(true) {
        cout << "\n--- SMART PARKING SYSTEM ---\n";
        cout << "1. Park Vehicle\n";
        cout << "2. Remove Vehicle\n";
        cout << "3. Show Slots\n";
        cout << "4. View Records\n";
        cout << "5. Reserve Slot\n";
        cout << "6. Exit\n";
        cout << "Enter choice: ";
        cin >> choice;

        switch(choice) {
            case 1:
                manager.parkVehicle();
                break;

            case 2:
                manager.removeVehicle();
                break;

            case 3:
                manager.showSlots();
                break;

            case 4: {
                FileHandler f;
                f.readData();
                break;
            }

            case 5:
                return 0;

            default:
                cout << "Invalid choice\n";
        }
    }
}