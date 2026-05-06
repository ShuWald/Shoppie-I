"use client";



import { useState, useEffect } from "react";

import Sidebar from "../components/Sidebar";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  ArcElement,
  RadialLinearScale
} from 'chart.js';
import { Bar, Doughnut, Bubble } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  ArcElement,
  RadialLinearScale
);

export default function Home() {

  const [report, setReport] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);

  const [activeTab, setActiveTab] = useState("overview");

  const [sortBy, setSortBy] = useState("popScore");

  const [selectedPriorities, setSelectedPriorities] = useState(new Set(["all"]));

  const [selectedSortOptions, setSelectedSortOptions] = useState(new Set(["popScore"]));

  const [searchTerm, setSearchTerm] = useState("");

  const [expandedReports, setExpandedReports] = useState(new Set());

  const [expandedRecommendation, setExpandedRecommendation] = useState(null);

  const [page, setPage] = useState(1);

  const [pageSize, setPageSize] = useState(10);

  const [pageInput, setPageInput] = useState("1");

  const [pageSizeInput, setPageSizeInput] = useState("10");

  const [showPageSizeMenu, setShowPageSizeMenu] = useState(false);

  const [tempPageSize, setTempPageSize] = useState("10");

  const [visualData, setVisualData] = useState(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showPageSizeMenu && !event.target.closest('.pagination-dropdown')) {
        setShowPageSizeMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showPageSizeMenu]);

  const [visualLoading, setVisualLoading] = useState(false);

  const [visualError, setVisualError] = useState(null);



  useEffect(() => {
    console.log('useEffect triggered, activeTab:', activeTab);
    // Trigger pre-caching when dashboard loads
    triggerPreCaching();
    // Always fetch comprehensive insights on initial load, then switch to tab-specific
    fetchComprehensiveInsights();
  }, []);

  useEffect(() => {
    console.log('Tab change useEffect triggered, activeTab:', activeTab);
    // For tab changes after initial load
    if (activeTab === "overview") {
      console.log('Fetching comprehensive insights for overview tab');
      fetchComprehensiveInsights();
    } else if (activeTab === "visual") {
      console.log('Fetching comprehensive data for visual tab');
      fetchComprehensiveVisualData();
    } else {
      console.log('Fetching regular products for other tab');
      fetchTrendingProducts();
    }
  }, [activeTab]);

  const triggerPreCaching = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/pre-cache-first-pages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const result = await response.json();
      console.log('Pre-caching completed:', result);
    } catch (error) {
      console.error('Failed to start pre-caching:', error);
    }
  };



  const fetchComprehensiveInsights = async () => {
    console.log('fetchComprehensiveInsights called');
    // Fetch all products for comprehensive insights using batch processing
    setLoading(true);
    setError(null);
    
    try {
      console.log('Making batch API calls for comprehensive insights from all 326 products...');
      
      // Process all products in batches of 50 to avoid timeouts
      const batchSize = 50;
      const totalProducts = 326;
      const batches = Math.ceil(totalProducts / batchSize);
      
      let allEvaluations = [];
      let totalEvaluated = 0;
      
      for (let batch = 0; batch < batches; batch++) {
        const page = batch + 1;
        console.log(`Processing batch ${batch + 1}/${batches} (page ${page})`);
        
        const response = await fetch(`http://localhost:8000/api/evaluate-trending-products?page=${page}&page_size=${batchSize}&stream=false`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status} on batch ${batch + 1}`);
        }

        const report = await response.json();
        console.log(`Batch ${batch + 1} API response structure:`, Object.keys(report));
        
        // Check if report has the expected structure
        if (!report) {
          console.error(`Batch ${batch + 1}: Invalid response structure`, report);
          throw new Error(`Invalid response structure on batch ${batch + 1}`);
        }
        
        // Collect all evaluations from this batch with fallbacks
        const batchEvaluations = [
          ...(report.high_priority_products || []),
          ...(report.medium_priority_products || []),
          ...(report.low_priority_products || [])
        ];
        
        allEvaluations = [...allEvaluations, ...batchEvaluations];
        totalEvaluated += report.total_products_evaluated || 0;
        
        console.log(`Batch ${batch + 1} completed: ${batchEvaluations.length} products evaluated`);
      }
      
      console.log(`All batches completed: ${allEvaluations.length} total products evaluated`);
      
      // Generate comprehensive insights from all evaluations
      const comprehensiveInsights = generateComprehensiveInsights(allEvaluations);
      
      // Create comprehensive report
      const comprehensiveReport = {
        generated_at: new Date().toISOString(),
        total_products_evaluated: allEvaluations.length,
        page: 1,
        page_size: allEvaluations.length,
        total_products_available: totalProducts,
        total_pages: 1,
        high_priority_products: allEvaluations.filter(e => e.pop_relevance_score >= 70),
        medium_priority_products: allEvaluations.filter(e => e.pop_relevance_score >= 40 && e.pop_relevance_score < 70),
        low_priority_products: allEvaluations.filter(e => e.pop_relevance_score < 40),
        summary_insights: comprehensiveInsights,
      };
      
      console.log('Comprehensive insights generated:', comprehensiveInsights);
      setReport(comprehensiveReport);
      setLoading(false);
      
    } catch (err) {
      console.error('Error in fetchComprehensiveInsights:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const generateComprehensiveInsights = (evaluations) => {
    console.log('Generating insights from', evaluations.length, 'evaluations');
    const insights = [];
    
    if (!evaluations || evaluations.length === 0) {
      return ["No products evaluated"];
    }
    
    // Count categories
    const categories = {};
    evaluations.forEach(e => {
      const category = e.product.category;
      categories[category] = (categories[category] || 0) + 1;
    });
    
    // Top category
    const topCategory = Object.entries(categories).reduce((a, b) => a[1] > b[1] ? a : b);
    insights.push(`Most trending category: ${topCategory[0]} (${topCategory[1]} products)`);
    
    // Average scores
    const avgPopScore = evaluations.reduce((sum, e) => sum + e.pop_relevance_score, 0) / evaluations.length;
    insights.push(`Average PoP relevance score: ${avgPopScore.toFixed(1)}`);
    
    // Action distribution
    const actions = {};
    evaluations.forEach(e => {
      const action = e.suggested_action;
      actions[action] = (actions[action] || 0) + 1;
    });
    
    if (actions["Distribute existing product"]) {
      insights.push(`Distribute Existing: ${actions["Distribute existing product"]}`);
    }
    if (actions["Develop new PoP product"]) {
      insights.push(`Develop New: ${actions["Develop new PoP product"]}`);
    }
    if (actions["Not recommended - poor business alignment"]) {
      insights.push(`Not Recommended: ${actions["Not recommended - poor business alignment"]}`);
    }
    
    // Risk analysis
    const highRiskProducts = evaluations.filter(e => 
      e.risk_assessment.tariff_risk === "high" || 
      e.risk_assessment.fda_concern === "high"
    );
    if (highRiskProducts.length > 0) {
      insights.push(`FDA High Risk: ${highRiskProducts.filter(e => e.risk_assessment.fda_concern === "high").length}`);
    }
    
        
    // Top opportunity
    const topProduct = evaluations.reduce((a, b) => a.pop_relevance_score > b.pop_relevance_score ? a : b);
    insights.push(`Top opportunity: ${topProduct.product.name} (Score: ${topProduct.pop_relevance_score.toFixed(1)})`);
    
    return insights;
  };

  const fetchTrendingProducts = async (requestedPage = page, requestedPageSize = pageSize) => {

    const safePage = Math.max(1, Number(requestedPage) || 1);

    const safePageSize = Math.min(100, Math.max(1, Number(requestedPageSize) || 10));

    // Update the input fields to match requested values
    setPageInput(String(safePage));

    setPageSizeInput(String(safePageSize));

    setPage(safePage);

    setPageSize(safePageSize);

    const initialReport = {
      generated_at: new Date().toISOString(),
      total_products_evaluated: 0,
      page: safePage,
      page_size: safePageSize,
      total_products_available: 0,
      total_pages: 0,
      high_priority_products: [],
      medium_priority_products: [],
      low_priority_products: [],
      summary_insights: [],
    };

    try {

      setLoading(true);

      setError(null);

      setReport(initialReport);

      const params = new URLSearchParams({
        page: String(safePage),
        page_size: String(safePageSize),
        stream: "true",
      });

      const response = await fetch(`http://localhost:8000/api/evaluate-trending-products?${params.toString()}`);

      if (!response.ok) {

        throw new Error(`HTTP error! status: ${response.status}`);

      }

      if (!response.body) {
        const data = await response.json();
        setReport(data);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const appendEvaluation = (priority, evaluation) => {
        const bucketKey =
          priority === "high"
            ? "high_priority_products"
            : priority === "medium"
              ? "medium_priority_products"
              : "low_priority_products";

        setReport((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            total_products_evaluated: prev.total_products_evaluated + 1,
            [bucketKey]: [...prev[bucketKey], evaluation],
          };
        });
      };

      const applyStreamEvent = (event) => {
        if (!event || !event.type) return;

        if (event.type === "meta") {
          setReport((prev) => ({
            ...(prev || initialReport),
            page: event.page ?? safePage,
            page_size: event.page_size ?? safePageSize,
            total_products_available: event.total_products_available ?? 0,
            total_pages: event.total_pages ?? 0,
          }));
          return;
        }

        if (event.type === "evaluation" || event.type === "item") {
          appendEvaluation(event.priority, event.evaluation);
          return;
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);
            applyStreamEvent(event);
          } catch (e) {
            console.error("Failed to parse stream event:", line, e);
          }
        }
      }

    } catch (err) {

      setError(err.message);

    } finally {

      setLoading(false);

    }

  };

  const fetchComprehensiveVisualData = async () => {
    console.log('fetchComprehensiveVisualData called');
    // Fetch all products for visual analysis using batch processing
    setVisualLoading(true);
    setVisualError(null);
    
    try {
      console.log('Making batch API calls for comprehensive visual data from all 326 products...');
      
      // Process all products in batches of 50 to avoid timeouts
      const batchSize = 50;
      const totalProducts = 326;
      const batches = Math.ceil(totalProducts / batchSize);
      
      let allEvaluations = [];
      let totalEvaluated = 0;
      
      for (let batch = 0; batch < batches; batch++) {
        const page = batch + 1;
        console.log(`Processing visual batch ${batch + 1}/${batches} (page ${page})`);
        
        const response = await fetch(`http://localhost:8000/api/evaluate-trending-products?page=${page}&page_size=${batchSize}&stream=false`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status} on visual batch ${batch + 1}`);
        }

        const report = await response.json();
        console.log(`Visual batch ${batch + 1} API response structure:`, Object.keys(report));
        
        // Check if report has the expected structure
        if (!report) {
          console.error(`Visual batch ${batch + 1}: Invalid response structure`, report);
          throw new Error(`Invalid response structure on visual batch ${batch + 1}`);
        }
        
        // Collect all evaluations from this batch with fallbacks
        const batchEvaluations = [
          ...(report.high_priority_products || []),
          ...(report.medium_priority_products || []),
          ...(report.low_priority_products || [])
        ];
        
        allEvaluations = [...allEvaluations, ...batchEvaluations];
        totalEvaluated += report.total_products_evaluated || 0;
        
        console.log(`Visual batch ${batch + 1} completed: ${batchEvaluations.length} products evaluated`);
      }
      
      console.log(`All visual batches completed: ${allEvaluations.length} total products evaluated`);
      
      // Create comprehensive visual data structure
      const comprehensiveVisualData = {
        generated_at: new Date().toISOString(),
        total_products_evaluated: allEvaluations.length,
        page: 1,
        page_size: allEvaluations.length,
        total_products_available: totalProducts,
        total_pages: 1,
        high_priority_products: allEvaluations.filter(e => e.pop_relevance_score >= 70),
        medium_priority_products: allEvaluations.filter(e => e.pop_relevance_score >= 40 && e.pop_relevance_score < 70),
        low_priority_products: allEvaluations.filter(e => e.pop_relevance_score < 40),
      };
      
      console.log('Comprehensive visual data generated:', comprehensiveVisualData);
      setVisualData(comprehensiveVisualData);
      setVisualLoading(false);
      
    } catch (err) {
      console.error('Error in fetchComprehensiveVisualData:', err);
      setVisualError(err.message);
      setVisualLoading(false);
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

    if (action === "Distribute existing product") {

      return "text-blue-600 bg-blue-100";

    } else if (action === "Develop new PoP product") {

      return "text-purple-600 bg-purple-100";

    } else if (action === "Not recommended - poor business alignment") {

      return "text-red-600 bg-red-100";

    }

    return "text-gray-600 bg-gray-100";

  };



  const getRiskWeight = (riskType) => {

    // Display risk weights for better transparency

    const weights = {

      'tariff': '1.0x',

      'fda': '2.5x',  // Highest weight

      'supply_chain': '1.5x',

      'competition': '0.8x'

    };

    return weights[riskType] || '1.0x';

  };



  const sortProducts = (products) => {

    let processedProducts = [...products];

    // Apply filters first
    const filters = Array.from(selectedSortOptions);
    
    if (filters.includes("flagged")) {
      processedProducts = processedProducts.filter(product => product.risk_assessment.flags && product.risk_assessment.flags.length > 0);
    }
    
    if (filters.includes("distribute")) {
      processedProducts = processedProducts.filter(product => product.suggested_action === "Distribute existing product");
    }
    
    if (filters.includes("develop")) {
      processedProducts = processedProducts.filter(product => product.suggested_action === "Develop new PoP product");
    }
    
    if (filters.includes("notRecommended")) {
      processedProducts = processedProducts.filter(product => product.suggested_action === "Not recommended - poor business alignment");
    }

    // Apply sorting
    const sortOptions = Array.from(selectedSortOptions);
    
    // Default to popScore if no sorting options
    if (sortOptions.length === 0 || sortOptions.includes("popScore")) {
      return processedProducts.sort((a, b) => b.pop_relevance_score - a.pop_relevance_score);
    }
    
    // Apply alphabetical sorting if selected
    if (sortOptions.includes("alphabetical")) {
      processedProducts = processedProducts.sort((a, b) => a.product.name.localeCompare(b.product.name));
    }
    
    // Apply competition sorting if selected
    if (sortOptions.includes("competition")) {
      processedProducts = processedProducts.sort((a, b) => {
        const competitionOrder = { low: 0, medium: 1, high: 2 };
        return competitionOrder[a.risk_assessment.competition_risk] - competitionOrder[b.risk_assessment.competition_risk];
      });
    }

    return processedProducts;

  };



  const filterProductsBySearch = (products) => {
    if (!searchTerm.trim()) return products;
    
    const searchLower = searchTerm.toLowerCase();
    
    return products.filter(product => {
      // Search in product name
      if (product.product.name.toLowerCase().includes(searchLower)) {
        return true;
      }
      
      // Search in product category
      if (product.product.category.toLowerCase().includes(searchLower)) {
        return true;
      }
      
      // Search in trend keywords
      if (product.product.trend_keywords && product.product.trend_keywords.some(keyword => 
        keyword.toLowerCase().includes(searchLower)
      )) {
        return true;
      }
      
      // Search in description
      if (product.product.description && product.product.description.toLowerCase().includes(searchLower)) {
        return true;
      }
      
      // Search in suggested action
      if (product.suggested_action && product.suggested_action.toLowerCase().includes(searchLower)) {
        return true;
      }
      
      return false;
    });
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

        valueClass: "text-base font-bold text-gray-900" // Smaller font for category names with dark color

      };

    }

    if (insight.includes("Average PoP relevance score")) {

      const match = insight.match(/Average PoP relevance score: ([\d.]+)/);

      return {

        title: "Avg PoP Score",

        value: match ? parseFloat(match[1]).toFixed(1) : "N/A",

        subtitle: "across all products",

        valueClass: "text-2xl font-bold text-gray-900" // Match READY FOR DISTRIBUTION tile spacing with dark color

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

        valueClass: "text-base font-bold text-gray-900" // Smaller font for long product names with dark color

      };

    }

    // New insight types for decision categories
    if (insight.includes("Distribute Existing")) {
      const match = insight.match(/Distribute Existing: (\d+)/);
      return {
        title: "Ready to Distribute",
        value: match ? match[1] : "0",
        subtitle: "products ready for market",
        valueClass: "text-2xl font-bold text-blue-600"
      };
    }

    if (insight.includes("Develop New")) {
      const match = insight.match(/Develop New: (\d+)/);
      return {
        title: "Development Pipeline",
        value: match ? match[1] : "0", 
        subtitle: "products requiring development",
        valueClass: "text-2xl font-bold text-purple-600"
      };
    }

    if (insight.includes("Not Recommended")) {
      const match = insight.match(/Not Recommended: (\d+)/);
      return {
        title: "Not Recommended",
        value: match ? match[1] : "0",
        subtitle: "products with poor alignment", 
        valueClass: "text-2xl font-bold text-red-600"
      };
    }

    // Risk management insights
    if (insight.includes("FDA High Risk")) {
      const match = insight.match(/FDA High Risk: (\d+)/);
      return {
        title: "FDA High Risk",
        value: match ? match[1] : "0",
        subtitle: "products requiring regulatory review",
        valueClass: "text-2xl font-bold text-orange-600"
      };
    }

    if (insight.includes("Supply Chain Risk")) {
      const match = insight.match(/Supply Chain Risk: (\d+)/);
      return {
        title: "Supply Chain Risk",
        value: match ? match[1] : "0",
        subtitle: "products with supply chain challenges",
        valueClass: "text-2xl font-bold text-yellow-600"
      };
    }

    
    // Default fallback

    return {

      title: "Insight",

      value: insight,

      subtitle: "data point",

      valueClass: "text-base font-bold"

    };

  }


  if (loading && !report) {

    return (

      <div className="min-h-screen bg-gray-50 flex items-center justify-center">

        <div className="text-center">

          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>

          <p className="mt-4 text-gray-600">Analyzing trending health & wellness products...</p>

        </div>

      </div>

    );

  }



  if (error && !report) {

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
    <div className="h-screen bg-gray-50 flex overflow-hidden">
      {/* Sidebar */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        selectedPriorities={selectedPriorities}
        setSelectedPriorities={setSelectedPriorities}
        selectedSortOptions={selectedSortOptions}
        setSelectedSortOptions={setSelectedSortOptions}
      />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4">
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
              <div className="flex items-center gap-3">
                <button 
                  onClick={() => {
                    const newPage = Math.max(1, Number(pageInput) || 1);
                    const newPageSize = Math.min(100, Math.max(1, Number(pageSizeInput) || 10));
                    fetchTrendingProducts(newPage, newPageSize);
                  }}
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

        <main className="flex-1 w-full max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-6 md:py-8 overflow-y-auto">

        {loading && report && (
          <div className="mb-4 rounded-md border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700">
            Streaming evaluations... {report.total_products_evaluated} item(s) received.
          </div>
        )}

        {error && report && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div>
            {/* Summary Insights - New Design */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Insights</h2>
              {report?.summary_insights && report.summary_insights.length > 0 ? (
                <div className="grid grid-cols-3 gap-4">
                  {report.summary_insights.map((insight, index) => {
                    const cardData = parseInsightCard(insight);
                    return (
                      <div key={index} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                        <p className="text-base font-bold text-blue-700 mb-2 break-words">{cardData.title}</p>
                        <p className={`mb-2 leading-tight break-words ${cardData.valueClass || 'text-lg font-bold text-gray-900'}`}>{cardData.value}</p>
                        <p className="text-sm text-gray-700 leading-relaxed break-words">{cardData.subtitle}</p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500">No insights available</p>
                  <p className="text-sm text-gray-400">Loading data...</p>
                </div>
              )}
            </div>

            {/* Actionable Recommendations Panel */}
            <div className="mb-6 md:mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Actionable Recommendations</h2>
              <div className="bg-white rounded-lg shadow p-4 md:p-6 border border-gray-200">
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
                        <div 
                          key={index} 
                          className={`p-4 rounded-lg border-2 hover:shadow-md transition-all duration-200 cursor-pointer ${
                            rec.type === 'launch' ? 'bg-green-50 border-green-200 hover:border-green-300' :
                            rec.type === 'regulatory' ? 'bg-yellow-50 border-yellow-200 hover:border-yellow-300' :
                            'bg-blue-50 border-blue-200 hover:border-blue-300'
                          }`}
                          onClick={() => setExpandedRecommendation(expandedRecommendation === index ? null : index)}
                        >
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
                            <svg 
                              className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${expandedRecommendation === index ? 'rotate-180' : ''}`} 
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>
                          {expandedRecommendation === index && (
                            <div className="mt-4 pt-4 border-t border-gray-200">
                              {rec.type === 'launch' && (
                                <div className="space-y-2">
                                  <p className="text-xs font-semibold text-gray-700">Next Steps:</p>
                                  <ul className="text-xs text-gray-600 list-disc list-inside space-y-1">
                                    <li>Review product specifications and packaging requirements</li>
                                    <li>Prepare distribution channel strategy</li>
                                    <li>Conduct final quality assurance testing</li>
                                    <li>Set launch timeline and marketing budget</li>
                                  </ul>
                                </div>
                              )}
                              {rec.type === 'regulatory' && (
                                <div className="space-y-2">
                                  <p className="text-xs font-semibold text-gray-700">Compliance Review:</p>
                                  <ul className="text-xs text-gray-600 list-disc list-inside space-y-1">
                                    <li>Consult FDA guidelines for product classification</li>
                                    <li>Review tariff rates and import requirements</li>
                                    <li>Obtain necessary certifications and approvals</li>
                                    <li>Document all compliance measures for audit trail</li>
                                  </ul>
                                </div>
                              )}
                              {rec.type === 'expansion' && (
                                <div className="space-y-2">
                                  <p className="text-xs font-semibold text-gray-700">Expansion Strategy:</p>
                                  <ul className="text-xs text-gray-600 list-disc list-inside space-y-1">
                                    <li>Analyze market demand and competition in category</li>
                                    <li>Identify key distribution partners</li>
                                    <li>Develop category-specific marketing approach</li>
                                    <li>Set sales targets and growth metrics</li>
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}
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
            <div className="mb-6">
              {/* Search Bar and Pagination */}
              <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-4">
                <div className="relative w-full sm:w-96 lg:w-1/2">
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search products by name, category, or keywords..."
                    className="w-full px-4 py-2 pl-10 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-800 placeholder-gray-400 caret-gray-800"
                  />
                  <svg 
                    className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  {searchTerm && (
                    <button
                      onClick={() => setSearchTerm("")}
                      className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
                
                {/* Pagination Controls */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      if (page > 1) {
                        const newPage = page - 1;
                        setPageInput(String(newPage));
                        fetchTrendingProducts(newPage, pageSize);
                      }
                    }}
                    disabled={page <= 1}
                    className="p-2 rounded border border-gray-300 bg-white hover:bg-blue-600 hover:border-blue-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-all duration-200 shadow-sm hover:shadow-md"
                  >
                    <svg className="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  
                  <div className="relative pagination-dropdown">
                    <button
                      onClick={() => {
                        setShowPageSizeMenu(!showPageSizeMenu);
                        setTempPageSize(pageSizeInput);
                      }}
                      className="px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 transition-colors cursor-pointer hover:border-blue-400 hover:bg-blue-50"
                    >
                      <span className="text-sm text-gray-700">
                        {((page - 1) * pageSize) + 1}-{Math.min(page * pageSize, report?.total_products_available || 0)} of {report?.total_products_available || 0}
                      </span>
                    </button>
                    
                    {showPageSizeMenu && (
                      <div className="absolute top-full right-0 mt-1 w-48 bg-white border border-gray-300 rounded-lg shadow-lg z-10">
                        <div className="p-3">
                          <label className="block text-xs font-medium text-gray-700 mb-2">
                            Sample Size
                          </label>
                          <input
                            type="text"
                            inputMode="numeric"
                            value={tempPageSize}
                            onChange={(e) => setTempPageSize(e.target.value)}
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                const num = Math.min(100, Math.max(1, Number(tempPageSize) || 10));
                                setPageSizeInput(String(num));
                                setShowPageSizeMenu(false);
                                fetchTrendingProducts(1, num);
                              }
                            }}
                            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter size (1-100)"
                            autoFocus
                          />
                          <div className="flex justify-between mt-2">
                            <button
                              onClick={() => setShowPageSizeMenu(false)}
                              className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => {
                                const num = Math.min(100, Math.max(1, Number(tempPageSize) || 10));
                                setPageSizeInput(String(num));
                                setShowPageSizeMenu(false);
                                fetchTrendingProducts(1, num);
                              }}
                              className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              Apply
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={() => {
                      const totalPages = report?.total_pages || 1;
                      if (page < totalPages) {
                        const newPage = page + 1;
                        setPageInput(String(newPage));
                        fetchTrendingProducts(newPage, pageSize);
                      }
                    }}
                    disabled={page >= (report?.total_pages || 1)}
                    className="p-2 rounded border border-gray-300 bg-white hover:bg-blue-600 hover:border-blue-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-all duration-200 shadow-sm hover:shadow-md"
                  >
                    <svg className="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <div className="space-y-4">
              {/* Get and display filtered products */}
              {(() => {
                let allProducts = [];
                
                // Handle multiple priority selections
                const priorities = Array.from(selectedPriorities);
                
                if (priorities.includes("all")) {
                  allProducts = [
                    ...report.high_priority_products.map(p => ({...p, priority: "high"})),
                    ...report.medium_priority_products.map(p => ({...p, priority: "medium"})),
                    ...report.low_priority_products.map(p => ({...p, priority: "low"}))
                  ];
                } else {
                  if (priorities.includes("high")) {
                    allProducts = [
                      ...allProducts,
                      ...report.high_priority_products.map(p => ({...p, priority: "high"}))
                    ];
                  }
                  if (priorities.includes("medium")) {
                    allProducts = [
                      ...allProducts,
                      ...report.medium_priority_products.map(p => ({...p, priority: "medium"}))
                    ];
                  }
                  if (priorities.includes("low")) {
                    allProducts = [
                      ...allProducts,
                      ...report.low_priority_products.map(p => ({...p, priority: "low"}))
                    ];
                  }
                }

                // Apply search filter
                const searchedProducts = filterProductsBySearch(allProducts);
                const sortedProducts = sortProducts(searchedProducts);

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
                          getRiskWeight={getRiskWeight}
                        />
                      ))}
                    </div>
                  );
                } else {
                  return (
                    <div className="text-center py-12">
                      <div className="text-gray-400 text-lg">
                        {searchTerm.trim() 
                          ? `No products found matching "${searchTerm}". Try different keywords.`
                          : selectedSortOptions.has("flagged")
                          ? "No flagged products found."
                          : selectedSortOptions.has("distribute")
                          ? "No products recommended for distribution."
                          : selectedSortOptions.has("develop")
                          ? "No products recommended for development."
                          : selectedSortOptions.has("notRecommended")
                          ? "No products marked as not recommended."
                          : "No products found in the selected priority levels."
                        }
                      </div>
                      {searchTerm.trim() && (
                        <button
                          onClick={() => setSearchTerm("")}
                          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                          Clear Search
                        </button>
                      )}
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
            
            {visualLoading && (
              <div className="mb-4 rounded-md border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700">
                Loading comprehensive visual data from all 326 products...
              </div>
            )}
            
            {visualError && (
              <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
                Error loading visual data: {visualError}
              </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4 md:gap-6">
              {/* POP RELEVANCE SCORES BY PRODUCT - Chart.js Horizontal Bar Chart */}
              <div className="bg-white border border-gray-200 rounded-xl p-4 md:p-5">
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">PoP relevance scores by product</h3>
                <div className="flex flex-wrap gap-3 mb-3">
                  <div className="flex items-center gap-1.5 text-xs text-gray-600">
                    <span className="w-2.5 h-2.5 rounded-sm bg-green-600"></span>
                    <span>High priority</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-600">
                    <span className="w-2.5 h-2.5 rounded-sm bg-blue-500"></span>
                    <span>Medium priority</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-600">
                    <span className="w-2.5 h-2.5 rounded-sm bg-gray-500"></span>
                    <span>Needs development</span>
                  </div>
                </div>
                <div className="relative h-48 sm:h-52 lg:h-56">
                  <Bar
                    data={{
                      labels: [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products].map(p => p.product.name),
                      datasets: [{
                        label: 'PoP Score',
                        data: [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products].map(p => p.pop_relevance_score),
                        backgroundColor: [
                          ...(visualData || report).high_priority_products.map(() => '#1D9E75'),
                          ...(visualData || report).medium_priority_products.map(() => '#378ADD'),
                          ...(visualData || report).low_priority_products.map(() => '#888780')
                        ],
                        borderRadius: 4,
                        borderSkipped: false,
                      }]
                    }}
                    options={{
                      indexAxis: 'y',
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: { legend: { display: false } },
                      scales: {
                        x: { min: 0, max: 100, ticks: { font: { size: 11 } }, grid: { color: '#f0f0f0' } },
                        y: { grid: { display: false }, ticks: { font: { size: 11 } } }
                      }
                    }}
                  />
                </div>
              </div>

              {/* CATEGORY DISTRIBUTION - Chart.js Doughnut Chart */}
              <div className="bg-white border border-gray-200 rounded-xl p-4 md:p-5">
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">Category distribution</h3>
                <div className="flex flex-wrap gap-3 mb-3">
                  {(() => {
                    const categoryCounts = {};
                    [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products].forEach(product => {
                      const category = product.product.category;
                      categoryCounts[category] = (categoryCounts[category] || 0) + 1;
                    });
                    const categories = Object.keys(categoryCounts);
                    const uniqueColors = [
                      '#1D9E75', '#378ADD', '#EF9F27', '#D4537E', '#888780',
                      '#E24B4A', '#F59E0B', '#8B5CF6', '#10B981', '#F97316',
                      '#06B6D4', '#84CC16', '#A855F7', '#EC4899', '#14B8A6'
                    ];
                    const colors = categories.map((cat, index) => uniqueColors[index % uniqueColors.length]);
                    
                    return categories.map((category, index) => (
                      <div key={category} className="flex items-center gap-1.5 text-xs text-gray-600">
                        <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: colors[index] }}></span>
                        <span>{category}</span>
                      </div>
                    ));
                  })()}
                </div>
                <div className="relative h-48 sm:h-52 lg:h-56">
                  <Doughnut
                    data={{
                      labels: (() => {
                        const categoryCounts = {};
                        [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products].forEach(product => {
                          const category = product.product.category;
                          categoryCounts[category] = (categoryCounts[category] || 0) + 1;
                        });
                        return Object.keys(categoryCounts);
                      })(),
                      datasets: [{
                        data: (() => {
                          const categoryCounts = {};
                          [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products].forEach(product => {
                            const category = product.product.category;
                            categoryCounts[category] = (categoryCounts[category] || 0) + 1;
                          });
                          return Object.values(categoryCounts);
                        })(),
                        backgroundColor: (() => {
                          const categoryCounts = {};
                          [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products].forEach(product => {
                            const category = product.product.category;
                            categoryCounts[category] = (categoryCounts[category] || 0) + 1;
                          });
                          const categories = Object.keys(categoryCounts);
                          const uniqueColors = [
                            '#1D9E75', '#378ADD', '#EF9F27', '#D4537E', '#888780',
                            '#E24B4A', '#F59E0B', '#8B5CF6', '#10B981', '#F97316',
                            '#06B6D4', '#84CC16', '#A855F7', '#EC4899', '#14B8A6'
                          ];
                          return categories.map((cat, index) => uniqueColors[index % uniqueColors.length]);
                        })(),
                        borderWidth: 0,
                        hoverOffset: 6,
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      cutout: '60%',
                      plugins: { legend: { display: false } }
                    }}
                  />
                </div>
              </div>

              {/* MARKET GROWTH VS CONSUMER INTEREST - Chart.js Bubble Chart */}
              <div className="bg-white border border-gray-200 rounded-xl p-4 md:p-5">
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">Market growth vs consumer interest</h3>
                <div className="relative h-48 sm:h-52 lg:h-56">
                  <Bubble
                    data={{
                      datasets: [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products].map((product, index) => ({
                        label: product.product.name,
                        data: [{
                          x: product.product.market_growth_rate,
                          y: product.product.consumer_interest_score,
                          r: Math.max(5, Math.min(15, product.pop_relevance_score / 5))
                        }],
                        backgroundColor: [
                          '#1D9E75cc', '#378ADDcc', '#EF9F27cc', '#D4537Ecc', '#888780cc'
                        ][index % 5]
                      }))
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: { legend: { display: false } },
                      scales: {
                        x: { 
                          title: { display: true, text: 'Market growth (%)', font: { size: 11 } }, 
                          min: 0, 
                          max: 100,
                          ticks: { font: { size: 11 } }
                        },
                        y: { 
                          title: { display: true, text: 'Consumer interest', font: { size: 11 } }, 
                          min: 0, 
                          max: 100,
                          ticks: { font: { size: 11 } }
                        }
                      }
                    }}
                  />
                </div>
              </div>

              {/* RISK PROFILE BREAKDOWN - Chart.js Stacked Bar Chart */}
              <div className="bg-white border border-gray-200 rounded-xl p-4 md:p-5">
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">Risk profile breakdown</h3>
                <div className="flex flex-wrap gap-3 mb-3">
                  <div className="flex items-center gap-1.5 text-xs text-gray-600">
                    <span className="w-2.5 h-2.5 rounded-sm bg-green-600"></span>
                    <span>Low</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-600">
                    <span className="w-2.5 h-2.5 rounded-sm bg-yellow-500"></span>
                    <span>Medium</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-600">
                    <span className="w-2.5 h-2.5 rounded-sm bg-red-500"></span>
                    <span>High</span>
                  </div>
                </div>
                <div className="relative h-48 sm:h-52 lg:h-56">
                  <Bar
                    data={{
                      labels: ['Tariff', 'FDA', 'Supply', 'Competition'],
                      datasets: [
                        { 
                          label: 'Low',    
                          data: (() => {
                            const allProducts = [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products];
                            return [
                              allProducts.filter(p => p.risk_assessment.tariff_risk === 'low').length,
                              allProducts.filter(p => p.risk_assessment.fda_concern === 'low').length,
                              allProducts.filter(p => p.risk_assessment.supply_chain_risk === 'low').length,
                              allProducts.filter(p => p.risk_assessment.competition_risk === 'low').length
                            ];
                          })(), 
                          backgroundColor: '#1D9E75', 
                          borderRadius: 3 
                        },
                        { 
                          label: 'Medium', 
                          data: (() => {
                            const allProducts = [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products];
                            return [
                              allProducts.filter(p => p.risk_assessment.tariff_risk === 'medium').length,
                              allProducts.filter(p => p.risk_assessment.fda_concern === 'medium').length,
                              allProducts.filter(p => p.risk_assessment.supply_chain_risk === 'medium').length,
                              allProducts.filter(p => p.risk_assessment.competition_risk === 'medium').length
                            ];
                          })(), 
                          backgroundColor: '#EF9F27', 
                          borderRadius: 3 
                        },
                        { 
                          label: 'High',   
                          data: (() => {
                            const allProducts = [...(visualData || report).high_priority_products, ...(visualData || report).medium_priority_products, ...(visualData || report).low_priority_products];
                            return [
                              allProducts.filter(p => p.risk_assessment.tariff_risk === 'high').length,
                              allProducts.filter(p => p.risk_assessment.fda_concern === 'high').length,
                              allProducts.filter(p => p.risk_assessment.supply_chain_risk === 'high').length,
                              allProducts.filter(p => p.risk_assessment.competition_risk === 'high').length
                            ];
                          })(), 
                          backgroundColor: '#E24B4A', 
                          borderRadius: 3 
                        },
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: { legend: { display: false } },
                      scales: {
                        x: { stacked: true, grid: { display: false }, ticks: { font: { size: 11 } } },
                        y: { stacked: true, ticks: { stepSize: 1, font: { size: 11 } } }
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        


        {/* Report Metadata */}
        <div className="bg-white rounded-lg shadow p-6 mt-8">
          <div className="flex flex-col md:flex-row md:justify-between gap-2 text-sm text-gray-600">
            <span>Total Products Evaluated: {report.total_products_evaluated}</span>
            <span>
              Viewing Page {report.page} of {Math.max(report.total_pages || 0, 1)}
              {" "}(page size {report.page_size}, total available {report.total_products_available})
            </span>
            <span>Generated: {new Date(report.generated_at).toLocaleString()}</span>
          </div>
        </div>

      </main>
      </div>
    </div>
  );
}

function ProductCard({ evaluation, getScoreColor, getScoreBgColor, getRiskColor, getActionColor, getRiskWeight, priority, expandedReports, toggleReportExpansion, formatCategoryName }) {

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
                <div className="text-xs text-blue-600 font-medium">Weight: {getRiskWeight('tariff')}</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${getRiskColor(risk_assessment.fda_concern)}`}>
                  {risk_assessment.fda_concern.toUpperCase()}
                </div>
                <div className="text-xs text-gray-600">FDA Concern</div>
                <div className="text-xs text-red-600 font-medium">Weight: {getRiskWeight('fda')}</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${getRiskColor(risk_assessment.supply_chain_risk)}`}>
                  {risk_assessment.supply_chain_risk.toUpperCase()}
                </div>
                <div className="text-xs text-gray-600">Supply Chain</div>
                <div className="text-xs text-orange-600 font-medium">Weight: {getRiskWeight('supply_chain')}</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${getRiskColor(risk_assessment.competition_risk)}`}>
                  {risk_assessment.competition_risk.toUpperCase()}
                </div>
                <div className="text-xs text-gray-600">Competition</div>
                <div className="text-xs text-gray-600 font-medium">Weight: {getRiskWeight('competition')}</div>
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
                      : suggested_action === "Develop new PoP product"
                      ? `Requires new product development cycle. Estimated time to market: 12-18 months. 
                         Initial investment focus on R&D, formulation, and regulatory compliance.`
                      : `Poor business alignment. Not recommended for investment. 
                         Consider alternative opportunities with better strategic fit.`
                    }
                    Confidence level: {confidence_score.toFixed(0)}% in projected outcomes.
                  </p>
                </div>
              </div>
            </div>

            {/* Confidence Score Analysis */}
            <div className="bg-white rounded-lg p-3 border border-blue-200">
              <h6 className="font-medium text-gray-900 text-sm mb-2">Confidence Analysis</h6>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600">Overall Confidence:</span>
                  <span className={`font-medium ${getScoreColor(confidence_score)}`}>
                    {confidence_score.toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Data Quality:</span>
                  <span className="font-medium text-gray-900">
                    {product.description && product.description.length > 20 ? 'High' : 'Medium'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Trend Consistency:</span>
                  <span className="font-medium text-gray-900">
                    {Math.abs(product.trend_score - product.market_growth_rate) < 20 ? 'Consistent' : 'Variable'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Risk Uncertainty:</span>
                  <span className={`font-medium ${risk_assessment.fda_concern === 'high' ? 'text-red-600' : 'text-green-600'}`}>
                    {risk_assessment.fda_concern === 'high' ? 'High' : risk_assessment.fda_concern === 'medium' ? 'Medium' : 'Low'}
                  </span>
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
                    {suggested_action === "Distribute existing product" ? '3-6 months' 
                      : suggested_action === "Develop new PoP product" ? '12-18 months'
                      : 'Not applicable'}
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

