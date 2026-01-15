import React from 'react';
import { Clock, AlertCircle, Smile } from 'lucide-react';

const EmailList = ({ emails, onSelect, selectedId }) => {
    const getUrgencyColor = (urgency) => {
        switch (urgency) {
            case 'high': return 'bg-red-100 text-red-700 border-red-200';
            case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
            default: return 'bg-green-100 text-green-700 border-green-200';
        }
    };

    return (
        <div className="w-full md:w-1/3 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 h-full overflow-y-auto">
            <div className="p-4 border-b border-gray-200 dark:border-gray-800">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Inbox</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">{emails.length} pending reviews</p>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {emails.map((email) => (
                    <div
                        key={email.id}
                        onClick={() => onSelect(email)}
                        className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${selectedId === email.id ? 'bg-blue-50 dark:bg-gray-800 border-l-4 border-blue-500' : 'border-l-4 border-transparent'
                            }`}
                    >
                        <div className="flex justify-between items-start mb-1">
                            <h3 className="font-medium text-gray-900 dark:text-gray-100 truncate w-3/4">{email.sender}</h3>
                            <span className="text-xs text-gray-400">
                                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        </div>
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 truncate">{email.subject}</h4>
                        <div className="flex space-x-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full border ${getUrgencyColor(email.classification?.urgency)}`}>
                                {email.classification?.urgency || 'low'}
                            </span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600">
                                {email.classification?.intent || 'general'}
                            </span>
                        </div>
                    </div>
                ))}
                {emails.length === 0 && (
                    <div className="p-8 text-center text-gray-500">
                        All caught up! 🎉
                    </div>
                )}
            </div>
        </div>
    );
};

export default EmailList;
