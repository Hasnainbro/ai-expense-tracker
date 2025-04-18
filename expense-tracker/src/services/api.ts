// src/services/api.ts

/**
 * Service for communicating with the expense tracker backend API
 */
export const API_URL = 'http://localhost:5000';

export interface ExpenseData {
  category: string;
  amount: number;
  date: string;
  description: string;
}

export interface ExpenseSummary {
  total_spent: number;
  top_category: string;
  category_breakdown: Record<string, number>;
}

export interface FormatData {
  format_type: string;
  value: string;
  target: string;
  sheet_name?: string;
}

/**
 * Process a natural language query through the backend
 */
export const processQuery = async (query: string): Promise<any> => {
  try {
    const response = await fetch(`${API_URL}/process_query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error processing query:', error);
    throw error;
  }
};

/**
 * Add a new expense (structured data)
 */
export const addExpense = async (expenseData: ExpenseData): Promise<any> => {
  try {
    const response = await fetch(`${API_URL}/add_expense`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(expenseData),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error adding expense:', error);
    throw error;
  }
};

/**
 * Add a new expense using natural language text
 */
export const addExpenseByText = async (text: string): Promise<any> => {
  try {
    const response = await fetch(`${API_URL}/add_expense`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error adding expense by text:', error);
    throw error;
  }
};

/**
 * Get expenses, optionally filtered by category
 */
export const getExpenses = async (category?: string): Promise<any> => {
  try {
    const url = category 
      ? `${API_URL}/get_expenses?category=${encodeURIComponent(category)}` 
      : `${API_URL}/get_expenses`;
      
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching expenses:', error);
    throw error;
  }
};

/**
 * Get expense summary data
 */
export const getExpenseSummary = async (): Promise<ExpenseSummary> => {
  try {
    const response = await fetch(`${API_URL}/expense_summary`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.summary;
  } catch (error) {
    console.error('Error fetching expense summary:', error);
    throw error;
  }
};

/**
 * Format the spreadsheet using natural language text
 */
export const formatSheet = async (text: string): Promise<any> => {
  try {
    const response = await fetch(`${API_URL}/format_sheet`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error formatting sheet:', error);
    throw error;
  }
};

/**
 * Format the spreadsheet with structured data
 */
export const formatSheetWithData = async (formatData: FormatData): Promise<any> => {
  try {
    const response = await fetch(`${API_URL}/format_sheet`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        text: `Apply ${formatData.format_type} with value ${formatData.value} to ${formatData.target}${
          formatData.sheet_name ? ` in the ${formatData.sheet_name} sheet` : ''
        }` 
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error formatting sheet with data:', error);
    throw error;
  }
};