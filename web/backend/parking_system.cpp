#include <iostream>
#include <string>
#include <ctime>
#include <map>
#include <vector>
#include <cmath>

extern "C" {
    
    // Fee calculation based on time spent (in minutes), returned in INR
    double calculateFee(int minutes, bool isVIP) {
        double baseFee = 40.0; // Rs 40 base fee
        double hourlyRate = isVIP ? 60.0 : 100.0; // VIP gets discount
        
        if (minutes <= 15) {
            return 0.0; // Free for first 15 minutes
        }
        
        double hours = minutes / 60.0;
        double totalFee = baseFee + (hours * hourlyRate);
        
        return round(totalFee * 100.0) / 100.0; // Round to 2 decimal places
    }
    
    // Generate QR code data (simple hash-based approach)
    void generateQRCode(const char* vehicleNumber, const char* slotId, char* output) {
        std::string data = std::string(vehicleNumber) + "_" + std::string(slotId);
        unsigned long hash = 5381;
        
        for(char c : data) {
            hash = ((hash << 5) + hash) + c;
        }
        
        sprintf(output, "QR_%lu_%s", hash, vehicleNumber);
    }
    
    // Validate QR code
    bool validateQRCode(const char* qrCode, const char* vehicleNumber) {
        std::string qr(qrCode);
        std::string vehicle(vehicleNumber);
        
        // Check if vehicle number is in the QR code
        return qr.find(vehicle) != std::string::npos;
    }
    
    // Calculate time difference in minutes
    int calculateTimeDifference(long entryTime, long exitTime) {
        return (exitTime - entryTime) / 60; // Convert seconds to minutes
    }
    
    // Check if slot is available based on occupancy
    bool isSlotAvailable(int currentOccupancy, int maxCapacity) {
        return currentOccupancy < maxCapacity;
    }
    
    // Calculate discount for VIP
    double applyVIPDiscount(double originalFee) {
        return originalFee * 0.7; // 30% discount for VIP
    }
    
    // Estimate parking duration cost
    double estimateCost(int estimatedMinutes, bool isVIP) {
        return calculateFee(estimatedMinutes, isVIP);
    }
    
    // Priority scoring for slot allocation (distance-based)
    double calculateSlotPriority(double distance, bool isVIP, bool isAvailable) {
        if (!isAvailable) return -1.0;
        
        double priority = 100.0 - distance; // Closer is better
        if (isVIP) priority += 50.0; // VIP gets higher priority
        
        return priority;
    }
}
