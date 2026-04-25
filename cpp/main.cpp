#include "classes.h"

int main() {

    // Encapsulation + Composition:
    // ParkingManager object controls the entire system
    // Internally it uses slots, file handler, etc.
    ParkingManager manager;
    int choice;
  // Loop to continuously run the system (menu-driven program)
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
       // Control flow using switch-case
        switch(choice) {
            case 1:
             // Abstraction:
                // User does not know how parking is handled internally
                // ParkingManager manages allocation, fee, QR, etc.
                manager.parkVehicle();
                break;

            case 2:
              // Encapsulation:
                // Exit logic handled inside ParkingManager
                manager.removeVehicle();
                break;

            case 3:
            // SRP:
                // Slot display is delegated to SlotDisplay class internally
                manager.showSlots();
                break;

            case 4: {
                // Abstraction:
                // FileHandler hides file reading implementation
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