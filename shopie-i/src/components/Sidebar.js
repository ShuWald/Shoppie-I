"use client";

import { useState } from "react";

export default function Sidebar({ activeTab, setActiveTab, selectedPriorities, setSelectedPriorities, selectedSortOptions, setSelectedSortOptions }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const tabs = [
    { id: "overview", name: "Overview", icon: "dashboard" },
    { id: "products", name: "Product List", icon: "list" },
    { id: "visual", name: "Visual Data", icon: "chart" }
  ];

  const getIcon = (iconName) => {
    switch (iconName) {
      case "dashboard":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        );
      case "list":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        );
      case "chart":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`${isCollapsed ? 'w-16' : 'w-64'} bg-white shadow-lg border-r border-gray-200 h-screen flex flex-col transition-all duration-300`}>
      <div className="p-6 flex-shrink-0">
        <div className="flex items-center justify-between mb-6">
          {!isCollapsed && <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 rounded hover:bg-gray-100 transition-colors"
          >
            <svg 
              className={`w-5 h-5 text-gray-600 transition-transform duration-200 ${isCollapsed ? 'rotate-90' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
        <nav className={`space-y-2 ${isCollapsed ? 'hidden' : 'block'}`}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                activeTab === tab.id
                  ? "bg-blue-50 text-blue-600 border-l-4 border-blue-600"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <span className={activeTab === tab.id ? "text-blue-600" : "text-gray-400"}>
                {getIcon(tab.icon)}
              </span>
              <span className="font-medium">{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>
      
      {/* Product Sorting and Filters - Only visible on products tab */}
      {activeTab === "products" && !isCollapsed && (
        <div className="flex-1 p-6 border-t border-gray-200 overflow-y-auto">
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Products:</label>
              <div className="space-y-2">
                {[
                  { value: "all", label: "All Priorities" },
                  { value: "high", label: "High Priority" },
                  { value: "medium", label: "Medium Priority" },
                  { value: "low", label: "Low Priority" }
                ].map((option) => (
                  <label key={option.value} className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-1 rounded">
                    <input
                      type="checkbox"
                      checked={selectedPriorities.has(option.value)}
                      onChange={(e) => {
                        const newPriorities = new Set(selectedPriorities);
                        if (e.target.checked) {
                          // If "all" is selected, clear others
                          if (option.value === "all") {
                            newPriorities.clear();
                            newPriorities.add("all");
                          } else {
                            newPriorities.delete("all");
                            newPriorities.add(option.value);
                          }
                        } else {
                          newPriorities.delete(option.value);
                          // If no priorities selected, default to "all"
                          if (newPriorities.size === 0) {
                            newPriorities.add("all");
                          }
                        }
                        setSelectedPriorities(newPriorities);
                      }}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Sort by:</label>
              <div className="space-y-2">
                {[
                  { value: "popScore", label: "Sort by PoP Score" },
                  { value: "alphabetical", label: "Sort Alphabetically" },
                  { value: "competition", label: "Sort by Competition" },
                  { value: "flagged", label: "Show Flagged Only" },
                  { value: "distribute", label: "Distribute Only" },
                  { value: "develop", label: "Develop Only" },
                  { value: "notRecommended", label: "Not Recommended Only" }
                ].map((option) => (
                  <label key={option.value} className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-1 rounded">
                    <input
                      type="checkbox"
                      checked={selectedSortOptions.has(option.value)}
                      onChange={(e) => {
                        const newSortOptions = new Set(selectedSortOptions);
                        if (e.target.checked) {
                          newSortOptions.add(option.value);
                        } else {
                          newSortOptions.delete(option.value);
                          // If no sort options selected, default to popScore
                          if (newSortOptions.size === 0) {
                            newSortOptions.add("popScore");
                          }
                        }
                        setSelectedSortOptions(newSortOptions);
                      }}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
              {Array.from(selectedSortOptions).some(option => 
                ["distribute", "develop", "notRecommended"].includes(option)
              ) && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {Array.from(selectedSortOptions).map(option => {
                    if (["distribute", "develop", "notRecommended"].includes(option)) {
                      return (
                        <span key={option} className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                          option === "distribute" ? "text-blue-600 bg-blue-100" :
                          option === "develop" ? "text-purple-600 bg-purple-100" :
                          "text-red-600 bg-red-100"
                        }`}>
                          {option === "distribute" ? "Distribute" :
                           option === "develop" ? "Develop" :
                           "Not Recommended"}
                        </span>
                      );
                    }
                    return null;
                  })}
                </div>
              )}
            </div>
            
                      </div>
        </div>
      )}
    </div>
  );
}
