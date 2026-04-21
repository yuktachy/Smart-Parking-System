#include <iostream>
#include <string>
#include <cmath>
#include <cstdio>

extern "C" {

    double calculateFee(int minutes, bool isVIP) {
        if (minutes <= 15) return 0.0;

        double ratePerHour = 20.0;
        double fee = ceil(minutes / 60.0) * ratePerHour;

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

    bool validateQRCode(const char* qrCode, const char* vehicleNumber, const char* slotId) {
        std::string qr(qrCode);
        std::string expected = std::string(vehicleNumber) + "_" + std::string(slotId);

        return qr.find(expected) != std::string::npos;
    }

    int calculateTimeDifference(long entryTime, long exitTime) {
        if (exitTime < entryTime) return 0;
        return (exitTime - entryTime) / 60;
    }

    bool isSlotAvailable(int currentOccupancy, int maxCapacity) {
        return currentOccupancy < maxCapacity;
    }

    double calculateSlotPriority(double distance, bool isVIP, bool isAvailable) {
        if (!isAvailable) return -1.0;

        double priority = 100.0 - distance;
        if (isVIP) priority += 30.0;

        return priority;
    }
}