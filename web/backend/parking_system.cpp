#include <iostream>
#include <string>
#include <cmath>
#include <cstdio>
// extern "C":
// Ensures compatibility with C / other languages (like Python, C#)
// Removes C++ name mangling (important for system integration)
extern "C" {

    // Abstraction:
    // Hides fee calculation logic from the user
    // Can be used inside ParkingSystem classes
    double calculateFee(int minutes, bool isVIP) {
        if (minutes <= 15) return 0.0;

        double ratePerHour = 20.0;
        // Encapsulation (logic grouping):
        // Fee calculation based on time
        double fee = ceil(minutes / 60.0) * ratePerHour;

        // Conditional behavior (can relate to polymorphism if moved to classes)
        if (isVIP) {
            fee *= 0.7;
        }

        return fee;
    }

    void generateQRCode(const char* vehicleNumber, const char* slotId, char* output) {
        std::string data = std::string(vehicleNumber) + "_" + std::string(slotId);
        unsigned long hash = 5381;

        for (char c : data) {
            hash = ((hash << 5) + hash) + c;
        }

        snprintf(output, 100, "QR_%lu_%s_%s", hash, vehicleNumber, slotId);
    }
 // Abstraction:
    // Validates QR code without exposing internal checking logic
    bool validateQRCode(const char* qrCode, const char* vehicleNumber, const char* slotId) {
        std::string qr(qrCode);
        std::string expected = std::string(vehicleNumber) + "_" + std::string(slotId);

        return qr.find(expected) != std::string::npos;
    }

    // Abstraction:
    // Calculates time difference in minutes
    int calculateTimeDifference(long entryTime, long exitTime) {
        if (exitTime < entryTime) return 0;
        return (exitTime - entryTime) / 60;
    }
 // Abstraction:
    // Checks if parking slot is available
    bool isSlotAvailable(int currentOccupancy, int maxCapacity) {
        return currentOccupancy < maxCapacity;
    }
 // Abstraction:
    // Calculates priority of slot based on multiple factors
    double calculateSlotPriority(double distance, bool isVIP, bool isAvailable) {

        // If slot is not available → invalid priority
        if (!isAvailable) return -1.0;
// Encapsulated scoring logic
        double priority = 100.0 - distance;

        // VIP preference (business rule)
        if (isVIP) priority += 30.0;

        return priority;
    }
}