'use client'

import SlideEffect from "@/components/slide-effect"
import { Button } from "@/components/ui/button"
import Link from "next/link"

const settings = {
  title: 'Start Creating With AI Today',
  description: 'Join thousands of creators and brands using AI to generate content, connect with partners, and grow their audience. Start your free 30-day trial now - no credit card required.',
  CTA: {
    content: 'Start your free trial',
    href: '#'
  }
}

export default function CTA() {
  return (
    <SlideEffect isSpring={false} className="space-y-6 sm:space-y-7 md:space-y-8 lg:space-y-10 mx-auto text-center p-8 md:p-16 flex flex-col items-center justify-center rounded-2xl bg-secondary dark:bg-secondary">
      {/* Title */}
      <h2 className="text-2xl md:text-4xl lg:text-header capitalize font-medium leading-normal text-transparent bg-clip-text bg-gradient-to-b from-black to-black/60 dark:from-white dark:to-white/60">{settings.title}</h2>

      {/* Description */}
      <p className="px-0 sm:px-10 md:px-0 w-full max-w-full md:max-w-3/4 mx-auto text-sm lg:text-base">{settings.description}</p>

      {/* CTA */}
      <Link href={settings.CTA.href}>
        <Button className="w-full" size='lg'>{settings.CTA.content}</Button>
      </Link>
    </SlideEffect>
  )
}