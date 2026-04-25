#include <iostream>
#include <vector>
#include <fstream>
using namespace std;

// ---------------- ABSTRACT BASE CLASS ----------------
// Abstraction:
// ParkingSystem is an abstract class (interface)
// It hides implementation and forces derived classes to define behavior
class ParkingSystem {
public:
    // Pure virtual functions (runtime polymorphism)
    virtual void allocateSlot(int &slot, vector<class ParkingSlot>& slots) = 0;
    virtual double calculateFee(int hours) = 0;
    virtual void displayDetails() = 0;

    // Virtual destructor
    virtual ~ParkingSystem() {}
};

// ---------------- VEHICLE ---------------
// Encapsulation:
// Data (vehicleNumber, type) is kept private
// Access is provided through public methods
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
// Encapsulation:
// Represents a parking slot with properties
class ParkingSlot {
public:
    int slotID;
    bool isOccupied;
    bool isVIP;

    ParkingSlot(int id = 0, bool vip = false);
};

// ---------------- FILE HANDLER ----------------
// Abstraction + SRP:
// Handles only file operations (separate responsibility)
class FileHandler {
public:
    void writeData(string record);
    void readData();
};

// ---------------- DERIVED CLASSES ----------------
// Inheritance:
// CarParking inherits from ParkingSystem

// Polymorphism:
// Overrides base class functions with specific behavior
class CarParking : public ParkingSystem {
public:
    void allocateSlot(int &slot, vector<ParkingSlot>& slots) override;
    double calculateFee(int hours) override;
    void displayDetails() override;
};
// Inheritance + Polymorphism
class BikeParking : public ParkingSystem {
public:
    void allocateSlot(int &slot, vector<ParkingSlot>& slots) override;
    double calculateFee(int hours) override;
    void displayDetails() override;
};
// Inheritance + Polymorphism
class VIPParking : public ParkingSystem {
public:
    void allocateSlot(int &slot, vector<ParkingSlot>& slots) override;
    double calculateFee(int hours) override;
    void displayDetails() override;
};

// ---------------- QR ENTRY ----------------
// Abstraction:
// Only exposes QR generation, hides internal logic
class QREntry {
public:
    string generateQR(string vehicleNumber);
    
};

// ---------------- RESERVATION ----------------

// Encapsulation + SRP:
// Handles reservation logic separately
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

