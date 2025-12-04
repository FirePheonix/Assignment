'use client'

import SlideEffect from "@/components/slide-effect"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

const settings = {
  title: 'Frequently asked questions',
  faqs: [
    {
      question: 'How does the AI content generation work?',
      answer: 'Our platform uses advanced AI to generate brand-ready photos, videos, and captions instantly. Simply describe what you need, and our multi-modal AI creates professional content including images, videos, text, and even audio. You can also use AI influencers to create realistic brand mockups and test campaigns before going live.',
    },
    {
      question: 'How do I find the right brand or creator to collaborate with?',
      answer: 'Our Creator-Brand Marketplace uses smart AI matching based on niche, audience demographics, engagement metrics, and content style. Browse profiles, review analytics, and connect with partners that align perfectly with your goals. Built-in chat and collaboration tools make it easy to manage partnerships from start to finish.',
    },
    {
      question: 'Can I manage all my social media accounts in one place?',
      answer: 'Yes! Our platform lets you schedule and manage posts across multiple social platforms from one unified dashboard. Access detailed analytics and performance insights for all channels, and streamline your entire workflow from content creation to scheduling to analytics tracking.',
    },
    {
      question: 'What kind of analytics and insights do you provide?',
      answer: 'We offer AI-driven insights that dive deep into engagement metrics, conversions, and campaign results. Compare performance across all your social channels, understand what content resonates with your audience, and get actionable recommendations to improve your strategy and grow faster.',
    },
    {
      question: 'Is there a mobile app?',
      answer: 'Absolutely! Our platform works seamlessly on both web and mobile with a clean, native interface. Create content, schedule posts, respond to messages, and check analytics from anywhere. Everything syncs automatically so you can work on the go.',
    },
  ]
}

export default function FAQ() {
  return (
    <div id='faq' className="space-y-6 sm:space-y-7 md:space-y-8 lg:space-y-10 mx-auto text-center">
      {/* Title */}
      <SlideEffect>
        <h2 className="text-2xl md:text-4xl lg:text-header capitalize text-transparent bg-clip-text bg-gradient-to-b from-black to-black/60 dark:from-white dark:to-white/60 font-medium leading-normale">{settings.title}</h2>
      </SlideEffect>

      {/* Accordion */}
      <SlideEffect>
        <Accordion type="single" collapsible className="max-w-2xl mx-auto text-base text-black dark:text-white">
          {settings.faqs.map((faq, index) => (
            <AccordionItem key={index} value={index + '-item'}>
              <AccordionTrigger>{faq.question}</AccordionTrigger>
              <AccordionContent>{faq.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </SlideEffect>
    </div>
  )
}