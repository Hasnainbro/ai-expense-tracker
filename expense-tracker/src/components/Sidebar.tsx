import React, { useState } from "react";
import { Home, BarChart2, Calendar, Settings, Menu, X, DollarSign, PieChart, Clock } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SidebarProps {
  darkMode: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ darkMode }) => {
  const [expanded, setExpanded] = useState(false);
  const [activeItem, setActiveItem] = useState("Dashboard");

  const menuItems = [
    { name: "Dashboard", icon: <Home size={20} /> },
    { name: "Expenses", icon: <DollarSign size={20} /> },
    { name: "Analytics", icon: <BarChart2 size={20} /> },
    { name: "Budget", icon: <PieChart size={20} /> },
    { name: "History", icon: <Clock size={20} /> },
    { name: "Calendar", icon: <Calendar size={20} /> },
    { name: "Settings", icon: <Settings size={20} /> }
  ];

  const toggleSidebar = () => {
    setExpanded(!expanded);
  };

  const sidebarVariants = {
    expanded: { width: "240px" },
    collapsed: { width: "70px" }
  };

  return (
    <motion.div
      initial="collapsed"
      animate={expanded ? "expanded" : "collapsed"}
      variants={sidebarVariants}
      transition={{ duration: 0.3 }}
      className={`h-screen ${
        darkMode ? "bg-gray-900" : "bg-white"
      } shadow-lg z-10 relative overflow-hidden`}
    >
      <div className="flex justify-end p-4">
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onClick={toggleSidebar}
          className={`rounded-full p-2 ${
            darkMode ? "hover:bg-gray-800" : "hover:bg-gray-100"
          } transition-all`}
        >
          {expanded ? (
            <X size={20} className={darkMode ? "text-white" : "text-gray-800"} />
          ) : (
            <Menu size={20} className={darkMode ? "text-white" : "text-gray-800"} />
          )}
        </motion.button>
      </div>
      
      <div className="mt-4">
        {menuItems.map((item) => (
          <motion.div
            key={item.name}
            onClick={() => setActiveItem(item.name)}
            whileHover={{ x: 5 }}
            className={`flex items-center px-4 py-3 cursor-pointer ${
              activeItem === item.name
                ? darkMode
                  ? "bg-blue-900 bg-opacity-40 text-blue-400"
                  : "bg-blue-50 text-blue-600"
                : darkMode
                ? "text-gray-400 hover:text-white"
                : "text-gray-600 hover:text-gray-900"
            } transition-all`}
          >
            <div className="flex items-center justify-center w-8">
              {React.cloneElement(item.icon, {
                className: activeItem === item.name
                  ? "text-blue-500"
                  : darkMode ? "text-gray-400" : "text-gray-500"
              })}
            </div>
            
            <AnimatePresence>
              {expanded && (
                <motion.span
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: "auto" }}
                  exit={{ opacity: 0, width: 0 }}
                  className="ml-3 font-medium whitespace-nowrap overflow-hidden"
                >
                  {item.name}
                </motion.span>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
      
      <motion.div
        className={`absolute bottom-8 left-0 right-0 mx-auto flex justify-center ${
          !expanded && "scale-75"
        }`}
        animate={{
          y: [0, -5, 0],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          repeatType: "loop",
        }}
      >
        {expanded ? (
          <div className={`px-4 py-2 rounded-lg ${
            darkMode ? "bg-blue-900 bg-opacity-30" : "bg-blue-50"
          }`}>
            <p className={`text-sm ${darkMode ? "text-blue-400" : "text-blue-600"}`}>
              Pro Tip: Say "Add" to track expenses
            </p>
          </div>
        ) : (
          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
            darkMode ? "bg-blue-900 bg-opacity-30" : "bg-blue-50"
          }`}>
            <span className={darkMode ? "text-blue-400" : "text-blue-600"}>💡</span>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
};

export default Sidebar;