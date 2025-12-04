'use client'

import Card from "@/components/card"
import SlideEffect from "@/components/slide-effect"
import { Button } from "@/components/ui/button"
import { CircleCheck } from "lucide-react"

const settings = {
  title: 'Pricing',
  description: 'Start creating content with AI and connect with brands today. Get a free 30-day trial with no credit card required. Plans start at just $6 per month.',
  plan_1: {
    planName: 'basic',
    price: 6,
    currency: '$',
    description: 'Perfect for solo creators starting their content journey.',
    cta: 'start your free trial',
    features: [
      'AI Content Generation',
      'Basic Social Media Scheduling',
      '5 Platform Connections',
      'Standard Analytics Dashboard',
      'Creator Marketplace Access',
      'Multi-Modal Generation',
      'Mobile App Access',
      'Community Support',
      'Brand Mockup Tools'
    ]
  },
  plan_2: {
    planName: 'Plus',
    price: 12,
    currency: '$',
    description: 'For growing creators and small brand teams.',
    cta: 'start your free trial',
    features: [
      'Unlimited AI Generations',
      'Advanced Social Scheduling',
      'Unlimited Platform Connections',
      'AI Influencer Mockups',
      'Smart Brand Matching',
      'Campaign Performance Tracking',
      'Team Collaboration Tools',
      'Priority Support',
    ]
  },
  plan_3: {
    planName: 'Enterprise',
    price: 19,
    currency: '$',
    description: 'For established brands and creator agencies.',
    cta: 'start your free trial',
    features: [
      'White-Label Solutions',
      'Custom AI Model Training',
      'Dedicated Account Manager',
      'Advanced Analytics & Insights',
      'API Access',
      'Custom Integrations',
      'Personal Onboarding',
      'Priority Feature Requests',
    ]
  },
}

export default function Pricing() {
  return (
    <div id='pricing' className="space-y-6 sm:space-y-7 md:space-y-8 lg:space-y-10 mx-auto text-center">
      {/* Title */}
      <SlideEffect>
        <h2 className="text-2xl md:text-4xl lg:text-header capitalize text-transparent bg-clip-text bg-gradient-to-b from-black to-black/60 dark:from-white dark:to-white/60 font-medium leading-normal">{settings.title}</h2>
      </SlideEffect>

      {/* Description */}
      <SlideEffect className="px-2 sm:px-10 md:px-0 w-full md:max-w-3/4 mx-auto text-sm lg:text-base">{settings.description}</SlideEffect>

      {/* Pricing Plans */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* plan 1 */}
        <SlideEffect isSpring={false} delay={0.1} className="text-base">
          <Card className="bg-white dark:bg-muted">
            <div className="capitalize text-start text-black dark:text-white">{settings.plan_1.planName}</div>
            <div className="flex items-baseline gap-1">
              <span className="font-medium text-4xl text-black dark:text-white">{settings.plan_1.currency}{settings.plan_1.price}</span>
              <span className="text-sm">/month</span>
            </div>
            <Button className="w-full">{settings.plan_1.cta}</Button>
            <div className="text-start space-y-6">
              <p className="text-black dark:text-white text-sm">{settings.plan_1.description}</p>

              <div className="flex flex-col items-start gap-4 text-sm">
                {settings.plan_1.features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <CircleCheck className="text-primary" size={16} />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </SlideEffect>

        {/* plan 2 */}
        <SlideEffect isSpring={false} delay={0.2} className="flex flex-col gap-6 text-base">
          <Card className="bg-secondary dark:bg-secondary">
            <div className="w-full flex items-center gap-2 justify-between">
              <div className="capitalize text-start text-black dark:text-white">{settings.plan_2.planName}</div>
              <div className="text-xs bg-accent px-2 py-1 rounded-full text-black dark:text-black capitalize">most popular</div>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="font-medium text-4xl text-black dark:text-white">{settings.plan_2.currency}{settings.plan_2.price}</span>
              <span className="text-sm">/month</span>
            </div>
            <Button className="w-full">{settings.plan_2.cta}</Button>
            <div className="text-start space-y-6">
              <p className="text-black dark:text-white text-sm">{settings.plan_2.description}</p>

              <div className="flex flex-col items-start gap-4 text-sm">
                {settings.plan_2.features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <CircleCheck className="text-primary" size={16} />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </SlideEffect>

        {/* plan 3 */}
        <SlideEffect isSpring={false} delay={0.3} className="flex flex-col gap-6 text-base">
          <Card className="bg-white dark:bg-muted">
            <div className="capitalize text-start text-black dark:text-white">{settings.plan_3.planName}</div>
            <div className="flex items-baseline gap-1">
              <span className="font-medium text-4xl text-black dark:text-white">{settings.plan_3.currency}{settings.plan_3.price}</span>
              <span className="text-sm">/month</span>
            </div>
            <Button className="w-full">{settings.plan_3.cta}</Button>
            <div className="text-start space-y-6">
              <p className="text-black dark:text-white text-sm">{settings.plan_3.description}</p>

              <div className="flex flex-col items-start gap-4 text-sm">
                {settings.plan_3.features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <CircleCheck className="text-primary" size={16} />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </SlideEffect>
      </div>
    </div>
  )
}