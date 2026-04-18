"use client";



import { useState, useEffect } from "react";

import Sidebar from "../components/Sidebar";



export default function Home() {

  const [report, setReport] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);

  const [activeTab, setActiveTab] = useState("overview");

  const [sortBy, setSortBy] = useState("popScore");

  const [priorityFilter, setPriorityFilter] = useState("all");

  const [categoryFilter, setCategoryFilter] = useState("all");

  const [expandedReports, setExpandedReports] = useState(new Set());



  useEffect(() => {

    fetchTrendingProducts();

  }, []);



  const fetchTrendingProducts = async () => {

    try {

      setLoading(true);

      const response = await fetch("http://localhost:8000/api/evaluate-trending-products");

      if (!response.ok) {

        throw new Error(`HTTP error! status: ${response.status}`);

      }

      const data = await response.json();

      setReport(data);

    } catch (err) {

      setError(err.message);

    } finally {

      setLoading(false);

    }

  };



  const getScoreColor = (score) => {

    if (score >= 80) return "text-green-600";

    if (score >= 60) return "text-yellow-600";

    return "text-red-600";

  };



  const getScoreBgColor = (score) => {

    if (score >= 80) return "bg-green-100";

    if (score >= 60) return "bg-yellow-100";

    return "bg-red-100";

  };



  const getRiskColor = (risk) => {

    switch (risk) {

      case "low": return "text-green-600";

      case "medium": return "text-yellow-600";

      case "high": return "text-red-600";

      default: return "text-gray-600";

    }

  };



  const getActionColor = (action) => {

    return action === "Distribute existing product" 

      ? "text-blue-600 bg-blue-100" 

      : "text-purple-600 bg-purple-100";

  };



  const sortProducts = (products) => {

    const sortedProducts = [...products];

    switch (sortBy) {

      case "alphabetical":

        return sortedProducts.sort((a, b) => a.product.name.localeCompare(b.product.name));

      case "competition":

        return sortedProducts.sort((a, b) => {

          const competitionOrder = { low: 0, medium: 1, high: 2 };

          return competitionOrder[a.risk_assessment.competition_risk] - competitionOrder[b.risk_assessment.competition_risk];

        });

      case "flagged":

        return sortedProducts.filter(product => product.risk_assessment.flags && product.risk_assessment.flags.length > 0);

      case "popScore":

      default:

        return sortedProducts.sort((a, b) => b.pop_relevance_score - a.pop_relevance_score);

    }

  };



  const filterProductsByCategory = (products) => {

    if (categoryFilter === "all") return products;

    return products.filter(product => product.product.category.toLowerCase() === categoryFilter.toLowerCase());

  };



  const formatCategoryName = (name) => {

    return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

  };



  const getUniqueCategories = () => {

    const allProducts = [...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products];

    const categories = [...new Set(allProducts.map(p => p.product.category))];

    return categories.sort();

  };



  const toggleReportExpansion = (productId) => {

    setExpandedReports(prev => {

      const newSet = new Set(prev);

      if (newSet.has(productId)) {

        newSet.delete(productId);

      } else {

        newSet.add(productId);

      }

      return newSet;

    });

  };



  const parseInsightCard = (insight) => {

    // Parse insight strings into structured card data

    if (insight.includes("Most trending category")) {

      const match = insight.match(/Most trending category: (.+) \((\d+) products\)/);

      return {

        title: "Top Category",

        value: match ? match[1] : "N/A",

        subtitle: match ? `${match[2]} products` : "No data",

        valueClass: "text-base font-bold" // Smaller font for category names

      };

    }

    if (insight.includes("Average PoP relevance score")) {

      const match = insight.match(/Average PoP relevance score: ([\d.]+)/);

      return {

        title: "Avg PoP Score",

        value: match ? parseFloat(match[1]).toFixed(1) : "N/A",

        subtitle: "across all products",

        valueClass: "text-2xl font-bold" // Match READY FOR DISTRIBUTION tile spacing

      };

    }

    if (insight.includes("Products ready for distribution")) {

      const match = insight.match(/Products ready for distribution: (\d+)/);

      return {

        title: "Ready for Distribution",

        value: match ? match[1] : "0",

        subtitle: "products"

      };

    }

    if (insight.includes("Products requiring development")) {

      const match = insight.match(/Products requiring development: (\d+)/);

      return {

        title: "Needs Development",

        value: match ? match[1] : "0",

        subtitle: "products"

      };

    }

    if (insight.includes("High-risk products")) {

      const match = insight.match(/High-risk products requiring careful review: (\d+)/);

      return {

        title: "High-Risk Review",

        value: match ? match[1] : "0",

        subtitle: match && match[1] === "1" ? "product flagged" : "products flagged"

      };

    }

    if (insight.includes("Top opportunity")) {

      const match = insight.match(/Top opportunity: (.+) \(Score: ([\d.]+)\)/);

      return {

        title: "Top Opportunity",

        value: match ? match[1] : "N/A",

        subtitle: match ? `PoP score ${match[2]}` : "No score",

        valueClass: "text-base font-bold" // Smaller font for long product names

      };

    }

    // Default fallback

    return {

      title: "Insight",

      value: insight,

      subtitle: ""

    };

  };



  if (loading) {

    return (

      <div className="min-h-screen bg-gray-50 flex items-center justify-center">

        <div className="text-center">

          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>

          <p className="mt-4 text-gray-600">Analyzing trending health & wellness products...</p>

        </div>

      </div>

    );

  }



  if (error) {

    return (

      <div className="min-h-screen bg-gray-50 flex items-center justify-center">

        <div className="text-center">

          <p className="text-red-600 mb-4">Error: {error}</p>

          <button 

            onClick={fetchTrendingProducts}

            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"

          >

            Retry

          </button>

        </div>

      </div>

    );

  }



  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* Main Content */}
      <div className="flex-1">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-4">
                {/* Prince of Peace Logo */}
                <img 
                  src="/PoPLogo.webp" 
                  alt="Prince of Peace Logo" 
                  className="h-12 w-auto object-contain"
                />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    Product Trend Dashboard
                  </h1>
                  <p className="text-sm text-gray-600 mt-1">
                    Smart shopping assistant for business buyers
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <button 
                  onClick={fetchTrendingProducts}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Refresh Analysis
                </button>
                {/* User Profile Icon */}
                <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300 transition-colors cursor-pointer">
                  <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div>
            {/* Summary Insights */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Insights</h2>
              <div className="grid grid-cols-3 gap-4">
                {report.summary_insights.map((insight, index) => {
                  const cardData = parseInsightCard(insight);
                  return (
                    <div key={index} className="bg-white rounded-lg shadow p-4 border border-gray-200 hover:shadow-md transition-shadow">
                      <p className="text-sm text-gray-500 uppercase tracking-wide break-words">{cardData.title}</p>
                      <p className={`${cardData.valueClass || "text-2xl font-bold"} text-gray-900 mt-1 break-words`}>{cardData.value}</p>
                      <p className="text-sm text-gray-600 mt-1 break-words">{cardData.subtitle}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Actionable Recommendations Panel */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Actionable Recommendations</h2>
              <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
                <div className="space-y-4">
                  {/* Generate recommendations based on report data */}
                  {(() => {
                    const recommendations = [];
                    
                    // Get top high priority product for launch recommendation
                    if (report.high_priority_products && report.high_priority_products.length > 0) {
                      const topProduct = report.high_priority_products[0];
                      recommendations.push({
                        type: 'launch',
                        product: topProduct.product.name,
                        popScore: topProduct.pop_relevance_score.toFixed(1),
                        priority: 'high'
                      });
                    }

                    // Find products with high regulatory risks
                    const highRiskProducts = [...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products]
                      .filter(p => p.risk_assessment.fda_concern === 'high' || p.risk_assessment.tariff_risk === 'high')
                      .slice(0, 2);
                    
                    highRiskProducts.forEach(product => {
                      recommendations.push({
                        type: 'regulatory',
                        product: product.product.name,
                        priority: 'medium'
                      });
                    });

                    // Find top category for expansion
                    const categoryCounts = {};
                    [...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products].forEach(product => {
                      const category = product.product.category;
                      categoryCounts[category] = (categoryCounts[category] || 0) + 1;
                    });
                    
                    const topCategory = Object.entries(categoryCounts)
                      .sort(([,a], [,b]) => b - a)[0];
                    
                    if (topCategory) {
                      recommendations.push({
                        type: 'expansion',
                        category: topCategory[0],
                        count: topCategory[1],
                        priority: 'medium'
                      });
                    }

                    return recommendations.map((rec, index) => {
                      let recommendationText = '';
                      let summaryText = '';
                      let iconColor = '';
                      
                      if (rec.type === 'launch') {
                        recommendationText = `Prioritize launching: ${rec.product}`;
                        summaryText = `High PoP score (${rec.popScore || '85+'}) indicates strong market potential and low risk`;
                        iconColor = 'text-green-600 bg-green-100';
                      } else if (rec.type === 'regulatory') {
                        recommendationText = `Investigate regulatory risks for: ${rec.product}`;
                        summaryText = `FDA or tariff concerns identified - review compliance requirements before market entry`;
                        iconColor = 'text-yellow-600 bg-yellow-100';
                      } else if (rec.type === 'expansion') {
                        const formattedCategory = rec.category.split('_').map(word => 
                          word.charAt(0).toUpperCase() + word.slice(1)
                        ).join(' ');
                        recommendationText = `Explore expansion in: ${formattedCategory}`;
                        summaryText = `${rec.count || 'Multiple'} products in this category show strong growth trends`;
                        iconColor = 'text-blue-600 bg-blue-100';
                      }
                      
                      return (
                        <div key={index} className={`p-4 rounded-lg border-2 hover:shadow-md transition-all duration-200 ${
                          rec.type === 'launch' ? 'bg-green-50 border-green-200 hover:border-green-300' :
                          rec.type === 'regulatory' ? 'bg-yellow-50 border-yellow-200 hover:border-yellow-300' :
                          'bg-blue-50 border-blue-200 hover:border-blue-300'
                        }`}>
                          <div className="flex items-start">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0 ${iconColor} shadow-sm`}>
                              {rec.type === 'launch' && (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                                </svg>
                              )}
                              {rec.type === 'regulatory' && (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                              )}
                              {rec.type === 'expansion' && (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                              )}
                            </div>
                            <div className="flex-1">
                              <div className={`inline-block px-2 py-1 rounded text-xs font-semibold mb-2 ${
                                rec.type === 'launch' ? 'bg-green-100 text-green-800' :
                                rec.type === 'regulatory' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {rec.type === 'launch' ? 'LAUNCH' : 
                                 rec.type === 'regulatory' ? 'RISK REVIEW' : 
                                 'EXPANSION'}
                              </div>
                              <p className="text-sm font-bold text-gray-900 mb-1 leading-tight">{recommendationText}</p>
                              <p className="text-xs text-gray-600 leading-relaxed">{summaryText}</p>
                            </div>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "products" && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-2">
                <label htmlFor="priority-select" className="text-sm font-medium text-gray-700">Products:</label>
                <select
                  id="priority-select"
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-medium text-gray-900"
                >
                  <option value="all">All Products</option>
                  <option value="high">High Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="low">Low Priority</option>
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <label htmlFor="sort-select" className="text-sm font-medium text-gray-700">Sort:</label>
                <select
                  id="sort-select"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-900"
                >
                  <option value="popScore">PoP Score</option>
                  <option value="alphabetical">Alphabetical</option>
                  <option value="competition">Competition</option>
                  <option value="flagged">Flagged</option>
                </select>
              </div>
            </div>
            
            {/* Category Search Terms */}
            <div className="mb-6">
              <div className="text-sm font-medium text-gray-700 mb-3">Filter by Category:</div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setCategoryFilter("all")}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    categoryFilter === "all"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  All Categories
                </button>
                {getUniqueCategories().map((category) => (
                  <button
                    key={category}
                    onClick={() => setCategoryFilter(category)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      categoryFilter === category
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    {formatCategoryName(category)}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-4">
              {/* Get and display filtered products */}
              {(() => {
                let allProducts = [];
                
                if (priorityFilter === "all") {
                  allProducts = [
                    ...filterProductsByCategory(report.high_priority_products).map(p => ({...p, priority: "high"})),
                    ...filterProductsByCategory(report.medium_priority_products).map(p => ({...p, priority: "medium"})),
                    ...filterProductsByCategory(report.low_priority_products).map(p => ({...p, priority: "low"}))
                  ];
                } else if (priorityFilter === "high") {
                  allProducts = filterProductsByCategory(report.high_priority_products).map(p => ({...p, priority: "high"}));
                } else if (priorityFilter === "medium") {
                  allProducts = filterProductsByCategory(report.medium_priority_products).map(p => ({...p, priority: "medium"}));
                } else if (priorityFilter === "low") {
                  allProducts = filterProductsByCategory(report.low_priority_products).map(p => ({...p, priority: "low"}));
                }

                const sortedProducts = sortProducts(allProducts);

                if (sortedProducts.length > 0) {
                  return (
                    <div className="space-y-4">
                      {sortedProducts.map((evaluation, index) => (
                        <ProductCard 
                          key={`${evaluation.priority}-${index}`} 
                          evaluation={evaluation} 
                          priority={evaluation.priority}
                          expandedReports={expandedReports}
                          toggleReportExpansion={toggleReportExpansion}
                          formatCategoryName={formatCategoryName}
                          getScoreColor={getScoreColor}
                          getScoreBgColor={getScoreBgColor}
                          getRiskColor={getRiskColor}
                          getActionColor={getActionColor}
                        />
                      ))}
                    </div>
                  );
                } else {
                  return (
                    <div className="text-center py-12">
                      <div className="text-gray-400 text-lg">
                        {sortBy === "flagged" 
                          ? "No flagged products found."
                          : categoryFilter === "all" 
                            ? "No products found in this priority level."
                            : `No products found in "${categoryFilter}" category for this priority level.`
                        }
                      </div>
                    </div>
                  );
                }
              })()}
            </div>
          </div>
        )}

        {activeTab === "visual" && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Visual Data Analysis</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* POP RELEVANCE SCORES BY PRODUCT - Horizontal Bar Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">POP RELEVANCE SCORES BY PRODUCT</h3>
                <div className="space-y-3">
                  {report.high_priority_products.map((evaluation, index) => (
                    <div key={index} className="flex items-center">
                      <div className="w-32 text-sm text-gray-600 truncate">{evaluation.product.name}</div>
                      <div className="flex-1 mx-3">
                        <div className="bg-gray-200 rounded-full h-6 relative">
                          <div 
                            className="bg-green-500 h-6 rounded-full flex items-center justify-end pr-2"
                            style={{width: `${evaluation.pop_relevance_score}%`}}
                          >
                            <span className="text-xs text-white font-semibold">{evaluation.pop_relevance_score.toFixed(1)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {report.medium_priority_products.map((evaluation, index) => (
                    <div key={`med-${index}`} className="flex items-center">
                      <div className="w-32 text-sm text-gray-600 truncate">{evaluation.product.name}</div>
                      <div className="flex-1 mx-3">
                        <div className="bg-gray-200 rounded-full h-6 relative">
                          <div 
                            className="bg-yellow-500 h-6 rounded-full flex items-center justify-end pr-2"
                            style={{width: `${evaluation.pop_relevance_score}%`}}
                          >
                            <span className="text-xs text-white font-semibold">{evaluation.pop_relevance_score.toFixed(1)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {report.low_priority_products.filter(p => p.pop_relevance_score >= 50).map((evaluation, index) => (
                    <div key={`low-${index}`} className="flex items-center">
                      <div className="w-32 text-sm text-gray-600 truncate">{evaluation.product.name}</div>
                      <div className="flex-1 mx-3">
                        <div className="bg-gray-200 rounded-full h-6 relative">
                          <div 
                            className="bg-orange-500 h-6 rounded-full flex items-center justify-end pr-2"
                            style={{width: `${evaluation.pop_relevance_score}%`}}
                          >
                            <span className="text-xs text-white font-semibold">{evaluation.pop_relevance_score.toFixed(1)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-center space-x-6 mt-4">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">High Priority</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">Medium Priority</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-orange-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">Needs Development</span>
                  </div>
                </div>
              </div>

              {/* CATEGORY DISTRIBUTION - Donut Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">CATEGORY DISTRIBUTION</h3>
                <div className="flex items-center justify-center">
                  <div className="relative w-48 h-48">
                    {/* Simple donut chart using CSS */}
                    <div className="absolute inset-0 rounded-full border-8 border-blue-500 border-r-transparent border-b-transparent transform rotate-45"></div>
                    <div className="absolute inset-0 rounded-full border-8 border-green-500 border-l-transparent border-b-transparent transform -rotate-45"></div>
                    <div className="absolute inset-0 rounded-full border-8 border-yellow-500 border-t-transparent border-r-transparent transform rotate-12"></div>
                    <div className="absolute inset-0 rounded-full border-8 border-purple-500 border-l-transparent border-t-transparent transform -rotate-12"></div>
                    <div className="absolute inset-8 bg-white rounded-full flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">{report.total_products_evaluated}</div>
                        <div className="text-xs text-gray-600">Total</div>
                      </div>
                    </div>
                  </div>
                  <div className="ml-8 space-y-2">
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-700">Herbal supplement</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-700">Beverage</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-700">Functional food</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-purple-500 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-700">Topical</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* MARKET GROWTH VS CONSUMER INTEREST - Scatter Plot */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">MARKET GROWTH VS CONSUMER INTEREST</h3>
                <div className="relative h-64 bg-gray-50 rounded-lg p-4">
                  <div className="absolute bottom-0 left-0 w-full h-px bg-gray-300"></div>
                  <div className="absolute top-0 left-0 w-full h-px bg-gray-300"></div>
                  <div className="absolute bottom-0 left-0 h-full w-px bg-gray-300"></div>
                  <div className="absolute bottom-0 right-0 h-full w-px bg-gray-300"></div>
                  
                  {/* Plot points */}
                  {[...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products].map((evaluation, index) => (
                    <div
                      key={index}
                      className={`absolute w-3 h-3 rounded-full transform -translate-x-1/2 -translate-y-1/2 ${
                        evaluation.pop_relevance_score >= 75 ? 'bg-green-500' :
                        evaluation.pop_relevance_score >= 60 ? 'bg-yellow-500' : 'bg-orange-500'
                      }`}
                      style={{
                        left: `${evaluation.product.market_growth_rate}%`,
                        bottom: `${evaluation.product.consumer_interest_score}%`
                      }}
                      title={`${evaluation.product.name}: Growth ${evaluation.product.market_growth_rate}%, Interest ${evaluation.product.consumer_interest_score}%`}
                    ></div>
                  ))}
                  
                  {/* Axis labels */}
                  <div className="absolute bottom-2 left-2 text-xs text-gray-600">0</div>
                  <div className="absolute bottom-2 right-2 text-xs text-gray-600">100%</div>
                  <div className="absolute top-2 left-2 text-xs text-gray-600">100%</div>
                  <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 text-xs text-gray-600 -mb-4">Market Growth</div>
                  <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -rotate-90 text-xs text-gray-600 -ml-8">Consumer Interest</div>
                </div>
              </div>

              {/* RISK PROFILE BREAKDOWN - Stacked Bar Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">RISK PROFILE BREAKDOWN</h3>
                <div className="space-y-3">
                  {['Tariff', 'FDA', 'Supply', 'Competition'].map((riskType, index) => {
                    const lowCount = [...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products]
                      .filter(p => {
                        const risk = p.risk_assessment;
                        if (riskType === 'Tariff') return risk.tariff_risk === 'low';
                        if (riskType === 'FDA') return risk.fda_concern === 'low';
                        if (riskType === 'Supply') return risk.supply_chain_risk === 'low';
                        if (riskType === 'Competition') return risk.competition_risk === 'low';
                        return false;
                      }).length;
                    
                    const mediumCount = [...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products]
                      .filter(p => {
                        const risk = p.risk_assessment;
                        if (riskType === 'Tariff') return risk.tariff_risk === 'medium';
                        if (riskType === 'FDA') return risk.fda_concern === 'medium';
                        if (riskType === 'Supply') return risk.supply_chain_risk === 'medium';
                        if (riskType === 'Competition') return risk.competition_risk === 'medium';
                        return false;
                      }).length;
                    
                    const highCount = [...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products]
                      .filter(p => {
                        const risk = p.risk_assessment;
                        if (riskType === 'Tariff') return risk.tariff_risk === 'high';
                        if (riskType === 'FDA') return risk.fda_concern === 'high';
                        if (riskType === 'Supply') return risk.supply_chain_risk === 'high';
                        if (riskType === 'Competition') return risk.competition_risk === 'high';
                        return false;
                      }).length;
                    
                    const total = lowCount + mediumCount + highCount;
                    
                    return (
                      <div key={index} className="flex items-center">
                        <div className="w-20 text-sm text-gray-600">{riskType}</div>
                        <div className="flex-1 mx-3">
                          <div className="bg-gray-200 rounded-full h-6 flex">
                            {lowCount > 0 && (
                              <div 
                                className="bg-green-500 h-6 rounded-l-full flex items-center justify-center"
                                style={{width: `${(lowCount/total)*100}%`}}
                              >
                                {lowCount > 0 && <span className="text-xs text-white">{lowCount}</span>}
                              </div>
                            )}
                            {mediumCount > 0 && (
                              <div 
                                className="bg-yellow-500 h-6 flex items-center justify-center"
                                style={{width: `${(mediumCount/total)*100}%`}}
                              >
                                <span className="text-xs text-white">{mediumCount}</span>
                              </div>
                            )}
                            {highCount > 0 && (
                              <div 
                                className="bg-red-500 h-6 rounded-r-full flex items-center justify-center"
                                style={{width: `${(highCount/total)*100}%`}}
                              >
                                <span className="text-xs text-white">{highCount}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-center space-x-6 mt-4">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">Low Risk</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">Medium Risk</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">High Risk</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "trends" && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Trend Predictions</h2>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Emerging Trends Analysis</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                      </div>
                      <h4 className="font-semibold text-gray-900">Herbal Supplements</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">Strong upward trend with 85% market confidence</p>
                    <div className="flex items-center text-xs text-green-600">
                      <span className="font-medium">+24% growth expected</span>
                    </div>
                  </div>
                  
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                        <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                      </div>
                      <h4 className="font-semibold text-gray-900">Functional Beverages</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">Moderate growth with seasonal variations</p>
                    <div className="flex items-center text-xs text-yellow-600">
                      <span className="font-medium">+12% growth expected</span>
                    </div>
                  </div>
                  
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                      <h4 className="font-semibold text-gray-900">Topical Products</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">Steady demand with niche opportunities</p>
                    <div className="flex items-center text-xs text-blue-600">
                      <span className="font-medium">+8% growth expected</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Seasonal Forecast</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Q1 2026</span>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                          <div className="bg-blue-500 h-2 rounded-full" style={{width: "65%"}}></div>
                        </div>
                        <span className="text-sm text-gray-600">High demand</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Q2 2026</span>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                          <div className="bg-green-500 h-2 rounded-full" style={{width: "85%"}}></div>
                        </div>
                        <span className="text-sm text-gray-600">Peak season</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Q3 2026</span>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                          <div className="bg-yellow-500 h-2 rounded-full" style={{width: "70%"}}></div>
                        </div>
                        <span className="text-sm text-gray-600">Moderate</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Q4 2026</span>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                          <div className="bg-purple-500 h-2 rounded-full" style={{width: "90%"}}></div>
                        </div>
                        <span className="text-sm text-gray-600">Holiday peak</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}



        {/* Report Metadata */}
        <div className="bg-white rounded-lg shadow p-6 mt-8">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Total Products Evaluated: {report.total_products_evaluated}</span>
            <span>Generated: {new Date(report.generated_at).toLocaleString()}</span>
          </div>
        </div>

      </main>
      </div>
    </div>
  );
}

function ProductCard({ evaluation, getScoreColor, getScoreBgColor, getRiskColor, getActionColor, priority, expandedReports, toggleReportExpansion, formatCategoryName }) {

  const { product, pop_relevance_score, risk_assessment, suggested_action, reasoning, confidence_score } = evaluation;

  const isExpanded = expandedReports.has(product.name);



  const getPriorityTag = (priority) => {

    switch (priority) {

      case "high":

        return "bg-green-100 text-green-800";

      case "medium":

        return "bg-yellow-100 text-yellow-800";

      case "low":

        return "bg-gray-100 text-gray-800";

      default:

        return "bg-gray-100 text-gray-800";

    }

  };



  return (

    <div className="bg-white rounded-lg shadow p-6">

      <div className="flex justify-between items-start mb-4">

        <div className="flex-1">

          <div className="flex items-center gap-2 mb-1">

            <h3 className="text-lg font-semibold text-gray-900">{product.name}</h3>

            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPriorityTag(priority)}`}>

              {priority.charAt(0).toUpperCase() + priority.slice(1)}

            </span>

            <button

              onClick={() => toggleReportExpansion(product.name)}

              className="text-blue-600 hover:text-blue-800 text-sm font-medium underline"

            >

              {isExpanded ? "Hide report" : "View full report"}

            </button>

          </div>

          <p className="text-sm text-gray-600 mt-1">{product.description}</p>

          <div className="flex flex-wrap gap-2 mt-2">

            <span className="px-2 py-1 bg-gray-100 text-xs rounded text-gray-700">

              {formatCategoryName(product.category)}

            </span>

            <span className="px-2 py-1 bg-gray-100 text-xs rounded text-gray-700">

              Source: {product.source}

            </span>

          </div>

        </div>

        <div className="text-right ml-4">

          <div className={`px-3 py-1 rounded-lg ${getScoreBgColor(pop_relevance_score)}`}>

            <span className={`text-lg font-bold ${getScoreColor(pop_relevance_score)}`}>

              {pop_relevance_score.toFixed(1)}

            </span>

          </div>

          <p className="text-xs text-gray-600 mt-1">PoP Score</p>

        </div>

      </div>



      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">

        <div>

          <p className="text-xs text-gray-600">Trend Score</p>

          <p className="text-sm font-semibold text-gray-900">{product.trend_score}</p>

        </div>

        <div>

          <p className="text-xs text-gray-600">Market Growth</p>

          <p className="text-sm font-semibold text-gray-900">{product.market_growth_rate}%</p>

        </div>

        <div>

          <p className="text-xs text-gray-600">Consumer Interest</p>

          <p className="text-sm font-semibold text-gray-900">{product.consumer_interest_score}</p>

        </div>

        <div>

          <p className="text-xs text-gray-600">Confidence</p>

          <p className="text-sm font-semibold text-gray-900">{confidence_score.toFixed(0)}%</p>

        </div>

      </div>



      <div className="mb-4">

        <p className="text-xs text-gray-600 mb-2">Risk Assessment</p>

        <div className="flex flex-wrap gap-2">

          <span className={`px-2 py-1 text-xs rounded ${getRiskColor(risk_assessment.tariff_risk)}`}>

            Tariff: {risk_assessment.tariff_risk}

          </span>

          <span className={`px-2 py-1 text-xs rounded ${getRiskColor(risk_assessment.fda_concern)}`}>

            FDA: {risk_assessment.fda_concern}

          </span>

          <span className={`px-2 py-1 text-xs rounded ${getRiskColor(risk_assessment.supply_chain_risk)}`}>

            Supply: {risk_assessment.supply_chain_risk}

          </span>

          <span className={`px-2 py-1 text-xs rounded ${getRiskColor(risk_assessment.competition_risk)}`}>

            Competition: {risk_assessment.competition_risk}

          </span>

        </div>

        {risk_assessment.flags.length > 0 && (

          <div className="mt-2">

            <p className="text-xs text-gray-600 mb-1">Flags:</p>

            <div className="flex flex-wrap gap-1">

              {risk_assessment.flags.map((flag, index) => (

                <span key={index} className="px-2 py-1 bg-red-100 text-xs rounded text-red-700">

                  {flag}

                </span>

              ))}

            </div>

          </div>

        )}

      </div>



      <div className="flex justify-between items-center">

        <div className="flex-1">

          <span className={`px-3 py-1 text-sm rounded-lg font-medium whitespace-nowrap inline-block ${getActionColor(suggested_action)}`}>

            {suggested_action}

          </span>

        </div>

        <div className="text-right ml-4">

          <p className="text-xs text-gray-600">Reasoning</p>

          <p className="text-sm text-gray-700">{reasoning}</p>

        </div>

      </div>

      {/* Detailed Report Section */}
      {isExpanded && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">Detailed Product Analysis</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Product Details */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-900 mb-3">Product Information</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Product Name:</span>
                  <span className="font-medium text-gray-900">{product.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Category:</span>
                  <span className="font-medium text-gray-900">{formatCategoryName(product.category)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Source:</span>
                  <span className="font-medium text-gray-900">{product.source}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Description:</span>
                  <span className="font-medium text-gray-900 max-w-xs">{product.description}</span>
                </div>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-900 mb-3">Performance Metrics</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">PoP Score:</span>
                  <span className={`font-bold ${getScoreColor(pop_relevance_score)}`}>{pop_relevance_score.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Trend Score:</span>
                  <span className="font-medium text-gray-900">{product.trend_score}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Market Growth:</span>
                  <span className="font-medium text-gray-900">{product.market_growth_rate}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Consumer Interest:</span>
                  <span className="font-medium text-gray-900">{product.consumer_interest_score}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Confidence Level:</span>
                  <span className="font-medium text-gray-900">{confidence_score.toFixed(0)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Assessment Details */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h5 className="font-semibold text-gray-900 mb-3">Risk Assessment</h5>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className={`text-lg font-bold ${getRiskColor(risk_assessment.tariff_risk)}`}>
                  {risk_assessment.tariff_risk.toUpperCase()}
                </div>
                <div className="text-xs text-gray-600">Tariff Risk</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${getRiskColor(risk_assessment.fda_concern)}`}>
                  {risk_assessment.fda_concern.toUpperCase()}
                </div>
                <div className="text-xs text-gray-600">FDA Concern</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${getRiskColor(risk_assessment.supply_chain_risk)}`}>
                  {risk_assessment.supply_chain_risk.toUpperCase()}
                </div>
                <div className="text-xs text-gray-600">Supply Chain</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${getRiskColor(risk_assessment.competition_risk)}`}>
                  {risk_assessment.competition_risk.toUpperCase()}
                </div>
                <div className="text-xs text-gray-600">Competition</div>
              </div>
            </div>
            
            {risk_assessment.flags.length > 0 && (
              <div>
                <h6 className="font-medium text-gray-900 mb-2">Risk Flags:</h6>
                <div className="flex flex-wrap gap-2">
                  {risk_assessment.flags.map((flag, index) => (
                    <span key={index} className="px-2 py-1 bg-red-100 text-xs rounded text-red-700">
                      {flag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Recommendation */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h5 className="font-semibold text-gray-900 mb-3">Recommendation</h5>
            <div className="mb-3">
              <span className={`px-3 py-1 text-sm rounded-lg font-medium whitespace-nowrap inline-block ${getActionColor(suggested_action)}`}>
                {suggested_action}
              </span>
            </div>
            <div className="mb-4">
              <h6 className="font-medium text-gray-900 mb-2">Detailed Reasoning:</h6>
              <p className="text-sm text-gray-700 mb-3">{reasoning}</p>
              
              {/* Additional Analysis */}
              <div className="space-y-3">
                <div className="border-l-4 border-blue-400 pl-3">
                  <h6 className="font-medium text-gray-900 text-sm mb-1">Market Analysis:</h6>
                  <p className="text-sm text-gray-600">
                    This product shows a {product.market_growth_rate}% market growth rate with {product.consumer_interest_score}% consumer interest, 
                    indicating {product.market_growth_rate > 70 ? 'strong' : product.market_growth_rate > 40 ? 'moderate' : 'limited'} market potential. 
                    The trend score of {product.trend_score} suggests {product.trend_score > 70 ? 'high' : product.trend_score > 40 ? 'moderate' : 'low'} consumer demand.
                  </p>
                </div>
                
                <div className="border-l-4 border-yellow-400 pl-3">
                  <h6 className="font-medium text-gray-900 text-sm mb-1">Risk Assessment:</h6>
                  <p className="text-sm text-gray-600">
                    Risk factors include {risk_assessment.tariff_risk} tariff risk, {risk_assessment.fda_concern} FDA concerns, 
                    {risk_assessment.supply_chain_risk} supply chain challenges, and {risk_assessment.competition_risk} competitive pressure.
                    {risk_assessment.flags.length > 0 && ` Key concerns: ${risk_assessment.flags.join(', ')}.`}
                    Overall risk profile is {risk_assessment.tariff_risk === 'low' && risk_assessment.fda_concern === 'low' && risk_assessment.supply_chain_risk === 'low' && risk_assessment.competition_risk === 'low' ? 'favorable' : 'moderate to high'}.
                  </p>
                </div>
                
                <div className="border-l-4 border-green-400 pl-3">
                  <h6 className="font-medium text-gray-900 text-sm mb-1">Strategic Fit:</h6>
                  <p className="text-sm text-gray-600">
                    With a PoP relevance score of {pop_relevance_score.toFixed(1)}, this product {pop_relevance_score >= 80 ? 'strongly aligns' : pop_relevance_score >= 60 ? 'moderately aligns' : 'has limited alignment'} 
                    with Prince of Peace's brand and market position. 
                    The {formatCategoryName(product.category)} category shows {pop_relevance_score >= 70 ? 'strong' : pop_relevance_score >= 50 ? 'moderate' : 'emerging'} performance 
                    in our portfolio.
                  </p>
                </div>
                
                <div className="border-l-4 border-purple-400 pl-3">
                  <h6 className="font-medium text-gray-900 text-sm mb-1">Implementation Considerations:</h6>
                  <p className="text-sm text-gray-600">
                    {suggested_action === "Distribute existing product" 
                      ? `Leverage current supply chain and distribution networks. Estimated time to market: 3-6 months. 
                         Initial investment focus on marketing and inventory management.`
                      : `Requires new product development cycle. Estimated time to market: 12-18 months. 
                         Investment needed for R&D, testing, and regulatory compliance.`
                    }
                    Confidence level: {confidence_score.toFixed(0)}% in projected outcomes.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Key Metrics Summary */}
            <div className="bg-white rounded-lg p-3 border border-blue-200">
              <h6 className="font-medium text-gray-900 text-sm mb-2">Key Success Indicators:</h6>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600">Market Potential:</span>
                  <span className={`font-medium ${getScoreColor(product.market_growth_rate)}`}>
                    {product.market_growth_rate > 70 ? 'High' : product.market_growth_rate > 40 ? 'Medium' : 'Low'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Risk Level:</span>
                  <span className={`font-medium ${getRiskColor(risk_assessment.competition_risk)}`}>
                    {risk_assessment.competition_risk === 'low' ? 'Low' : risk_assessment.competition_risk === 'medium' ? 'Medium' : 'High'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Brand Fit:</span>
                  <span className={`font-medium ${getScoreColor(pop_relevance_score)}`}>
                    {pop_relevance_score >= 80 ? 'Excellent' : pop_relevance_score >= 60 ? 'Good' : 'Moderate'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Timeline:</span>
                  <span className="font-medium text-gray-900">
                    {suggested_action === "Distribute existing product" ? '3-6 months' : '12-18 months'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>

  );

}

