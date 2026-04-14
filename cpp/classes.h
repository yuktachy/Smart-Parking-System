#include <iostream>
#include <vector>
#include <fstream>
using namespace std;

// ---------------- ABSTRACT BASE CLASS ----------------
class ParkingSystem {
public:
    virtual void allocateSlot(int &slot, vector<class ParkingSlot>& slots) = 0;
    virtual double calculateFee(int hours) = 0;
    virtual void displayDetails() = 0;
    virtual ~ParkingSystem() {}
};

// ---------------- VEHICLE ----------------
class Vehicle {
private:
    string vehicleNumber;
    string type;
public:
    Vehicle(string num = "", string t = "");
    string getVehicleNumber();
    string getType();
};

// ---------------- PARKING SLOT ----------------
class ParkingSlot {
public:
    int slotID;
    bool isOccupied;
    bool isVIP;

    ParkingSlot(int id = 0, bool vip = false);
};

// ---------------- FILE HANDLER ----------------
class FileHandler {
public:
    void writeData(string record);
    void readData();
};

// ---------------- DERIVED CLASSES ----------------
class CarParking : public ParkingSystem {
public:
    void allocateSlot(int &slot, vector<ParkingSlot>& slots) override;
    double calculateFee(int hours) override;
    void displayDetails() override;
};

class BikeParking : public ParkingSystem {
public:
    void allocateSlot(int &slot, vector<ParkingSlot>& slots) override;
    double calculateFee(int hours) override;
    void displayDetails() override;
};

class VIPParking : public ParkingSystem {
public:
    void allocateSlot(int &slot, vector<ParkingSlot>& slots) override;
    double calculateFee(int hours) override;
    void displayDetails() override;
};

// ---------------- QR ENTRY ----------------
class QREntry {
public:
    string generateQR(string vehicleNumber);
    
};

// ---------------- RESERVATION ----------------
class Reservation {
public:
    void reserveSlot(string vehicleNumber, int slot);
};

// ---------------- SLOT DISPLAY ----------------
class SlotDisplay {
public:
    void showSlots(vector<ParkingSlot> slots);
};

// ---------------- MANAGER ----------------
class ParkingManager {
private:
    vector<ParkingSlot> slots;
    FileHandler file;

public:
    ParkingManager();
    void parkVehicle();
    void removeVehicle();
    void showSlots();
};

