import React, { useState, useEffect } from 'react';
import { Send, RefreshCw, X, Check } from 'lucide-react';

const DraftEditor = ({ email, onAction }) => {
    const [draft, setDraft] = useState('');

    useEffect(() => {
        if (email?.draft?.draft) {
            setDraft(email.draft.draft);
        } else {
            setDraft(email?.generatedDraft || ''); // Fallback
        }
    }, [email]);

    if (!email) {
        return (
            <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900 text-gray-400">
                Select an email to view details
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col h-full bg-gray-50 dark:bg-gray-900 overflow-hidden">
            {/* Header */}
            <div className="p-6 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
                <h2 className="text-xl font-bold text-gray-800 dark:text-white mb-1">{email.subject}</h2>
                <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <span className="font-medium mr-2">From:</span> {email.sender}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Original Email */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                    <h3 className="text-xs uppercase tracking-wider text-gray-400 font-bold mb-4">Original Message</h3>
                    <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{email.body}</p>
                </div>

                {/* Draft Editor */}
                <div className="bg-indigo-50 dark:bg-gray-800 rounded-xl shadow-sm border border-indigo-100 dark:border-gray-600 p-6">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-xs uppercase tracking-wider text-indigo-500 font-bold">AI Suggested Response</h3>
                        <div className="flex space-x-2">
                            <button
                                onClick={() => onAction('regenerate', email)}
                                className="p-2 text-indigo-600 hover:bg-indigo-100 rounded-full transition-colors"
                                title="Regenerate"
                            >
                                <RefreshCw size={18} />
                            </button>
                        </div>
                    </div>
                    <textarea
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        className="w-full h-64 p-4 rounded-lg border border-gray-200 dark:border-gray-600 focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white dark:bg-gray-700 dark:text-white resize-none font-sans text-gray-700 leading-relaxed shadow-inner"
                    />
                </div>
            </div>

            {/* Action Bar */}
            <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
                <button
                    onClick={() => onAction('discard', email)}
                    className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg font-medium flex items-center transition-colors"
                >
                    <X size={18} className="mr-2" /> Discard
                </button>
                <button
                    onClick={() => onAction('approve', { ...email, finalDraft: draft })}
                    className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium flex items-center shadow-lg shadow-indigo-200 dark:shadow-none transition-all transform hover:scale-105"
                >
                    <Send size={18} className="mr-2" /> Approve & Send
                </button>
            </div>
        </div>
    );
};

export default DraftEditor;
