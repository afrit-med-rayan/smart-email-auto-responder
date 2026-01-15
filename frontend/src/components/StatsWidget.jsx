import React from 'react';
import { Mail, Zap, CheckCircle } from 'lucide-react';

const StatsWidget = ({ stats = { processed: 0, saved: 0, accuracy: 98 } }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center space-x-4">
                <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg text-blue-600 dark:text-blue-300">
                    <Mail size={24} />
                </div>
                <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Emails Processed</p>
                    <p className="text-2xl font-bold text-gray-800 dark:text-white">{stats.processed}</p>
                </div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center space-x-4">
                <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg text-purple-600 dark:text-purple-300">
                    <Zap size={24} />
                </div>
                <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Time Saved</p>
                    <p className="text-2xl font-bold text-gray-800 dark:text-white">{stats.saved} hrs</p>
                </div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center space-x-4">
                <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg text-green-600 dark:text-green-300">
                    <CheckCircle size={24} />
                </div>
                <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Accuracy</p>
                    <p className="text-2xl font-bold text-gray-800 dark:text-white">{stats.accuracy}%</p>
                </div>
            </div>
        </div>
    );
};

export default StatsWidget;
