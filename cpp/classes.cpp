#include "classes.h"

// ---------------- VEHICLE ----------------
Vehicle::Vehicle(string num, string t) {
    vehicleNumber = num;
    type = t;
}

string Vehicle::getVehicleNumber() {
    return vehicleNumber;
}

string Vehicle::getType() {
    return type;
}

// ---------------- PARKING SLOT ----------------
ParkingSlot::ParkingSlot(int id, bool vip) {
    slotID = id;
    isOccupied = false;
    isVIP = vip;
}

// ---------------- FILE HANDLER ----------------
void FileHandler::writeData(string record) {
    ofstream file("data.csv", ios::app);
    file << record << endl;
    file.close();
}

void FileHandler::readData() {
    ifstream file("data.csv");
    string line;
    while(getline(file, line)) {
        cout << line << endl;
    }
    file.close();

}


// ---------------- SLOT ALLOCATION LOGIC ----------------
void CarParking::allocateSlot(int &slot, vector<ParkingSlot>& slots) {
    for(auto &s : slots) {
        if(!s.isOccupied && !s.isVIP) {
            s.isOccupied = true;
            slot = s.slotID;
            return;
        }
    }
}

void BikeParking::allocateSlot(int &slot, vector<ParkingSlot>& slots) {
    for(auto &s : slots) {
        if(!s.isOccupied && !s.isVIP) {
            s.isOccupied = true;
            slot = s.slotID;
            return;
        }
    }
}

void VIPParking::allocateSlot(int &slot, vector<ParkingSlot>& slots) {
    for(auto &s : slots) {
        if(!s.isOccupied && s.isVIP) {
            s.isOccupied = true;
            slot = s.slotID;
            return;
        }
    }
}

// ---------------- FEE ----------------
double CarParking::calculateFee(int hours) { return hours * 50; }
double BikeParking::calculateFee(int hours) { return hours * 20; }
double VIPParking::calculateFee(int hours) { return hours * 100; }

// ---------------- DISPLAY ----------------
void CarParking::displayDetails() { cout << "Car Parking\n"; }
void BikeParking::displayDetails() { cout << "Bike Parking\n"; }
void VIPParking::displayDetails() { cout << "VIP Parking\n"; }

// ---------------- QR ENTRY ----------------
string QREntry::generateQR(string vehicleNumber) {
    return "QR_" + vehicleNumber;

}

// ---------------- RESERVATION ----------------
void Reservation::reserveSlot(string vehicleNumber, int slot) {
    ofstream file("reservation.csv", ios::app);
    file << vehicleNumber << "," << slot << endl;
    file.close();
    
}

// ---------------- SLOT DISPLAY ----------------
void SlotDisplay::showSlots(vector<ParkingSlot> slots) {
    for(auto s : slots) {
        cout << "Slot " << s.slotID 
             << (s.isOccupied ? " Occupied" : " Free") 
             << (s.isVIP ? " (VIP)" : "") << endl;
    }
}

// ---------------- MANAGER ----------------
ParkingManager::ParkingManager() {
    for(int i=1;i<=10;i++) {
        if(i <= 2)
            slots.push_back(ParkingSlot(i, true)); // VIP
        else
            slots.push_back(ParkingSlot(i, false));
    }
}

void ParkingManager::parkVehicle() {
    string num, type;
    int entryTime, exitTime;

    cout << "Enter Vehicle Number: ";
    cin >> num;
    cout << "Type (car/bike/vip): ";
    cin >> type;
    cout << "Entry Time: ";
    cin >> entryTime;
    cout << "Exit Time: ";
    cin >> exitTime;

    int hours = exitTime - entryTime;
    int slot = -1;

    ParkingSystem* p;

    if(type == "car")
        p = new CarParking();
    else if(type == "bike")
        p = new BikeParking();
    else
        p = new VIPParking();

    p->allocateSlot(slot, slots);
    double fee = p->calculateFee(hours);

    QREntry qrObj;
    string qr = qrObj.generateQR(num);

    file.writeData(num + "," + type + "," +
    to_string(slot) + "," +
    to_string(entryTime) + "," +
    to_string(exitTime) + "," +
    to_string(hours) + "," +
    to_string(fee) + "," +
    qr + "," +
    (type == "vip" ? "Yes" : "No")
);
    cout << "Allocated Slot: " << slot << endl;
    cout << "Fee: " << fee << endl;

    delete p;
}

void ParkingManager::removeVehicle() {
    cout << "Vehicle exited\n";
}

void ParkingManager::showSlots() {
    SlotDisplay s;
    s.showSlots(slots);
}