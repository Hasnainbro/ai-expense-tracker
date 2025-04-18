import React, { useState } from "react";
import { Plus, ChevronDown, ChevronUp, Filter, Download } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// Define ColorMapping interface
interface ColorMapping {
  bg: string;
  text: string;
  dark: string;
}

// Sample expense data
const sampleExpenses = [
  { id: 1, date: "2025-02-25", category: "Groceries", amount: 85.50, description: "Weekly shopping at Whole Foods" },
  { id: 2, date: "2025-02-24", category: "Dining", amount: 35.20, description: "Dinner with friends" },
  { id: 3, date: "2025-02-22", category: "Transport", amount: 45.00, description: "Uber rides" },
  { id: 4, date: "2025-02-20", category: "Shopping", amount: 129.99, description: "New headphones" },
  { id: 5, date: "2025-02-18", category: "Bills", amount: 85.00, description: "Electricity bill" },
];

// Category to color mapping
const categoryColors: Record<string, ColorMapping> = {
  Groceries: { bg: "bg-green-100", text: "text-green-800", dark: "bg-green-900 bg-opacity-30 text-green-400" },
  Dining: { bg: "bg-yellow-100", text: "text-yellow-800", dark: "bg-yellow-900 bg-opacity-30 text-yellow-400" },
  Transport: { bg: "bg-blue-100", text: "text-blue-800", dark: "bg-blue-900 bg-opacity-30 text-blue-400" },
  Shopping: { bg: "bg-purple-100", text: "text-purple-800", dark: "bg-purple-900 bg-opacity-30 text-purple-400" },
  Bills: { bg: "bg-red-100", text: "text-red-800", dark: "bg-red-900 bg-opacity-30 text-red-400" },
};

interface ExpenseListProps {
  darkMode: boolean;
}

const ExpenseList: React.FC<ExpenseListProps> = ({ darkMode }) => {
  const [expenses] = useState(sampleExpenses);
  const [sortBy, setSortBy] = useState("date");
  const [sortDirection, setSortDirection] = useState("desc");
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("All");

  type SortField = "date" | "amount";

  const toggleSort = (field: SortField): void => {
    if (sortBy === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortDirection("desc");
    }
  };

  interface ColorMapping {
    bg: string;
    text: string;
    dark: string;
  }

  const getCategoryStyle = (category: string): string => {
    const colors: ColorMapping =
      categoryColors[category] ||
      { bg: "bg-gray-100", text: "text-gray-800", dark: "bg-gray-800 text-gray-300" };
    return darkMode ? colors.dark : `${colors.bg} ${colors.text}`;
  };

  const filteredExpenses = selectedCategory === "All" 
    ? expenses 
    : expenses.filter(expense => expense.category === selectedCategory);

  const sortedExpenses = [...filteredExpenses].sort((a, b) => {
    if (sortBy === "date") {
      return sortDirection === "asc" 
        ? new Date(a.date).getTime() - new Date(b.date).getTime() 
        : new Date(b.date).getTime() - new Date(a.date).getTime();
    } else if (sortBy === "amount") {
      return sortDirection === "asc" ? a.amount - b.amount : b.amount - a.amount;
    }
    return 0;
  });

  const totalAmount = sortedExpenses.reduce((sum, expense) => sum + expense.amount, 0);

  const categories = ["All", ...new Set(expenses.map(expense => expense.category))];

  return (
    <div className={`h-full flex flex-col rounded-xl overflow-hidden ${
      darkMode ? "bg-gray-800 bg-opacity-50" : "bg-white bg-opacity-70"
    } backdrop-blur-sm shadow-lg`}>
      <div className="px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white flex justify-between items-center">
        <h2 className="font-semibold">Recent Expenses</h2>
        <div className="flex space-x-2">
          <motion.button 
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowFilters(!showFilters)}
            className="p-1 rounded-full bg-white bg-opacity-20 hover:bg-opacity-30"
          >
            <Filter size={16} />
          </motion.button>
          <motion.button 
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            className="p-1 rounded-full bg-white bg-opacity-20 hover:bg-opacity-30"
          >
            <Download size={16} />
          </motion.button>
        </div>
      </div>
      
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className={`p-3 ${darkMode ? "bg-gray-700" : "bg-gray-50"} flex flex-wrap gap-2`}>
              {categories.map(category => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                    selectedCategory === category
                      ? darkMode
                        ? "bg-blue-600 text-white"
                        : "bg-blue-500 text-white"
                      : darkMode
                      ? "bg-gray-600 text-gray-300 hover:bg-gray-500"
                      : "bg-white text-gray-600 hover:bg-gray-100"
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <div className="flex-1 overflow-y-auto">
        <table className="min-w-full">
          <thead className={darkMode ? "bg-gray-700" : "bg-gray-50"}>
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium tracking-wider">
                <button 
                  className="flex items-center space-x-1"
                  onClick={() => toggleSort("date")}
                >
                  <span>Date</span>
                  {sortBy === "date" && (
                    sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </button>
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium tracking-wider">Category</th>
              <th className="px-4 py-2 text-left text-xs font-medium tracking-wider">
                <button 
                  className="flex items-center space-x-1"
                  onClick={() => toggleSort("amount")}
                >
                  <span>Amount</span>
                  {sortBy === "amount" && (
                    sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </button>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            <AnimatePresence>
              {sortedExpenses.map((expense) => (
                <motion.tr
                  key={expense.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                  className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}
                >
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm">
                      {new Date(expense.date).toLocaleDateString()}
                    </div>
                    <div className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                      {expense.description}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getCategoryStyle(expense.category)}`}>
                      {expense.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                    ${expense.amount.toFixed(2)}
                  </td>
                </motion.tr>
              ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
      
      <div className={`p-4 border-t ${darkMode ? "border-gray-700" : "border-gray-200"} flex justify-between items-center`}>
        <div>
          <div className="text-sm font-medium">Total:</div>
          <div className={`text-lg font-bold ${darkMode ? "text-blue-400" : "text-blue-600"}`}>
            ${totalAmount.toFixed(2)}
          </div>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${
            darkMode 
              ? "bg-blue-600 hover:bg-blue-500" 
              : "bg-blue-500 hover:bg-blue-600"
          } text-white transition-colors`}
        >
          <Plus size={16} />
          <span>Add Expense</span>
        </motion.button>
      </div>
    </div>
  );
};

export default ExpenseList;