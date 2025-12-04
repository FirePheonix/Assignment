"use client";

import { 
  CreditCard, 
  Download, 
  Calendar, 
  DollarSign, 
  TrendingUp, 
  Package, 
  Receipt, 
  Plus,
  CheckCircle,
  Clock,
  XCircle
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface PlanFeature {
  text: string;
  included: boolean;
}

interface Plan {
  id: string;
  name: string;
  price: number;
  credits: number;
  features: PlanFeature[];
  popular?: boolean;
}

interface Transaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  credits: number;
  status: 'completed' | 'pending' | 'failed';
  invoice_url?: string;
}

const PLANS: Plan[] = [
  {
    id: 'starter',
    name: 'Starter Pack',
    price: 9.99,
    credits: 100,
    features: [
      { text: '100 AI Credits', included: true },
      { text: 'Basic Instagram Management', included: true },
      { text: 'Content Generation', included: true },
      { text: 'Email Support', included: true },
      { text: 'Advanced Analytics', included: false },
      { text: 'Priority Support', included: false },
    ]
  },
  {
    id: 'growth',
    name: 'Growth Pack',
    price: 29.99,
    credits: 350,
    features: [
      { text: '350 AI Credits', included: true },
      { text: 'Advanced Instagram Management', included: true },
      { text: 'Content Generation + Optimization', included: true },
      { text: 'Advanced Analytics', included: true },
      { text: 'Priority Email Support', included: true },
      { text: 'Custom Branding', included: false },
    ],
    popular: true
  },
  {
    id: 'pro',
    name: 'Pro Pack',
    price: 59.99,
    credits: 750,
    features: [
      { text: '750 AI Credits', included: true },
      { text: 'Full Instagram Suite', included: true },
      { text: 'AI Content Creation & Optimization', included: true },
      { text: 'Advanced Analytics & Reporting', included: true },
      { text: '24/7 Priority Support', included: true },
      { text: 'Custom Branding & White-label', included: true },
    ]
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 149.99,
    credits: 2000,
    features: [
      { text: '2000+ AI Credits', included: true },
      { text: 'Enterprise Instagram Management', included: true },
      { text: 'Custom AI Models & Training', included: true },
      { text: 'Advanced Analytics & API Access', included: true },
      { text: 'Dedicated Account Manager', included: true },
      { text: 'Full White-label & Custom Integration', included: true },
    ]
  }
];

const MOCK_TRANSACTIONS: Transaction[] = [
  {
    id: 'tx_001',
    date: '2024-11-29',
    description: 'Growth Pack - 350 AI Credits',
    amount: 29.99,
    credits: 350,
    status: 'completed',
    invoice_url: '/invoices/tx_001.pdf'
  },
  {
    id: 'tx_002', 
    date: '2024-11-15',
    description: 'Starter Pack - 100 AI Credits',
    amount: 9.99,
    credits: 100,
    status: 'completed',
    invoice_url: '/invoices/tx_002.pdf'
  },
  {
    id: 'tx_003',
    date: '2024-11-01',
    description: 'Pro Pack - 750 AI Credits',
    amount: 59.99,
    credits: 750,
    status: 'completed',
    invoice_url: '/invoices/tx_003.pdf'
  },
  {
    id: 'tx_004',
    date: '2024-10-28',
    description: 'Growth Pack - 350 AI Credits',
    amount: 29.99,
    credits: 350,
    status: 'pending'
  },
  {
    id: 'tx_005',
    date: '2024-10-15',
    description: 'Starter Pack - 100 AI Credits',
    amount: 9.99,
    credits: 100,
    status: 'failed'
  }
];

export default function BillingPage() {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Mock user data - in real app this would come from API
  const userCredits = {
    current: 245,
    total_purchased: 1450,
    total_used: 1205,
    last_updated: '2024-11-29'
  };

  const handlePurchase = async (planId: string) => {
    setIsLoading(true);
    setSelectedPlan(planId);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const plan = PLANS.find(p => p.id === planId);
      toast.success(`Successfully purchased ${plan?.name}! ${plan?.credits} credits added to your account.`);
      
      // In real app, redirect to payment processor or show success
    } catch (error) {
      toast.error('Payment failed. Please try again.');
    } finally {
      setIsLoading(false);
      setSelectedPlan(null);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusIcon = (status: Transaction['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getStatusColor = (status: Transaction['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-400 bg-green-500/10';
      case 'pending':
        return 'text-yellow-400 bg-yellow-500/10';
      case 'failed':
        return 'text-red-400 bg-red-500/10';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Billing & Credits</h1>
        <p className="text-gray-400 mt-1">
          Manage your AI credits and subscription
        </p>
      </div>

      {/* Credits Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <DollarSign className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h3 className="font-medium text-sm text-gray-300">Current Credits</h3>
              <p className="text-2xl font-bold text-purple-400">{userCredits.current}</p>
            </div>
          </div>
          <div className="text-xs text-gray-400">
            Last updated: {formatDate(userCredits.last_updated)}
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <TrendingUp className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="font-medium text-sm text-gray-300">Total Purchased</h3>
              <p className="text-2xl font-bold text-blue-400">{userCredits.total_purchased.toLocaleString()}</p>
            </div>
          </div>
          <div className="text-xs text-gray-400">
            Lifetime credits purchased
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <Package className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <h3 className="font-medium text-sm text-gray-300">Credits Used</h3>
              <p className="text-2xl font-bold text-green-400">{userCredits.total_used.toLocaleString()}</p>
            </div>
          </div>
          <div className="text-xs text-gray-400">
            Total credits consumed
          </div>
        </div>
      </div>

      {/* Usage Progress */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-bold mb-4">Credit Usage</h3>
        <div className="space-y-4">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-400">Available Credits</span>
            <span className="font-medium">{userCredits.current} remaining</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3">
            <div 
              className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full transition-all duration-500"
              style={{ 
                width: `${Math.max(10, (userCredits.current / (userCredits.current + 100)) * 100)}%` 
              }}
            />
          </div>
          <div className="text-xs text-gray-400">
            Consider purchasing more credits when you reach 50 credits or below
          </div>
        </div>
      </div>

      {/* Purchase Plans */}
      <div>
        <h2 className="text-2xl font-bold mb-6">Purchase More Credits</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`relative bg-white/5 border rounded-lg p-6 transition-all duration-300 hover:bg-white/10 ${
                plan.popular 
                  ? 'border-purple-500/50 ring-2 ring-purple-500/20' 
                  : 'border-white/10 hover:border-purple-500/30'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                    POPULAR
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-lg font-bold mb-2">{plan.name}</h3>
                <div className="text-3xl font-bold mb-1">
                  <span className="text-sm font-normal">$</span>
                  {plan.price}
                </div>
                <div className="text-sm text-gray-400 mb-4">
                  {plan.credits} AI Credits
                </div>
                <div className="text-xs text-purple-400 bg-purple-500/10 rounded-full px-3 py-1 inline-block">
                  ${(plan.price / plan.credits).toFixed(3)}/credit
                </div>
              </div>

              <div className="space-y-3 mb-6">
                {plan.features.map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    {feature.included ? (
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-gray-500 flex-shrink-0" />
                    )}
                    <span className={feature.included ? 'text-gray-300' : 'text-gray-500'}>
                      {feature.text}
                    </span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => handlePurchase(plan.id)}
                disabled={isLoading}
                className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed ${
                  plan.popular
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:opacity-90'
                    : 'bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 hover:border-purple-500/30'
                }`}
              >
                {isLoading && selectedPlan === plan.id ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    Processing...
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <Plus className="w-4 h-4" />
                    Purchase Now
                  </div>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Transaction History */}
      <div className="bg-white/5 border border-white/10 rounded-lg overflow-hidden">
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold">Transaction History</h3>
            <button className="text-sm text-purple-400 hover:text-purple-300 flex items-center gap-1">
              <Download className="w-4 h-4" />
              Export All
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-white/5">
              <tr>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Date</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Description</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Credits</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Amount</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Status</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {MOCK_TRANSACTIONS.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-white/5">
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span className="text-sm">{formatDate(transaction.date)}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm font-medium">{transaction.description}</div>
                    <div className="text-xs text-gray-400">Transaction ID: {transaction.id}</div>
                  </td>
                  <td className="p-4">
                    <span className="text-sm font-medium text-purple-400">
                      +{transaction.credits}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm font-medium">${transaction.amount}</span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(transaction.status)}
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(transaction.status)}`}>
                        {transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      {transaction.invoice_url && transaction.status === 'completed' && (
                        <button 
                          onClick={() => window.open(transaction.invoice_url, '_blank')}
                          className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
                        >
                          <Receipt className="w-3 h-3" />
                          Invoice
                        </button>
                      )}
                      {transaction.status === 'failed' && (
                        <button 
                          onClick={() => handlePurchase('retry')}
                          className="text-xs text-blue-400 hover:text-blue-300"
                        >
                          Retry
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {MOCK_TRANSACTIONS.length === 0 && (
          <div className="text-center py-12">
            <Receipt className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-400 mb-2">No transactions yet</h4>
            <p className="text-sm text-gray-500">
              Purchase your first credit pack to get started
            </p>
          </div>
        )}
      </div>

      {/* Billing Information */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-bold mb-4">Billing Information</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-400">
              Payment Method
            </label>
            <div className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-lg">
              <CreditCard className="w-5 h-5 text-gray-400" />
              <div>
                <div className="text-sm font-medium">**** **** **** 4242</div>
                <div className="text-xs text-gray-400">Expires 12/2025</div>
              </div>
              <button className="ml-auto text-xs text-purple-400 hover:text-purple-300">
                Update
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-400">
              Billing Address
            </label>
            <div className="space-y-2 text-sm text-gray-300">
              <div>John Doe</div>
              <div>123 Main Street, Apt 4B</div>
              <div>New York, NY 10001</div>
              <div>United States</div>
            </div>
            <button className="mt-2 text-xs text-purple-400 hover:text-purple-300">
              Update Address
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}