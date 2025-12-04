'use client'

import FadeEffect from "@/components/fade-effect";
import Navbar from "@/components/navbar";
import SlideEffect from "@/components/slide-effect";
import TextBlurEffect from "@/components/text-blur-effect";
import { Button } from "@/components/ui/button";
import { ArrowRight, Star } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { AnimatedTooltip } from "@/components/ui/animated-tooltip";

const settings = {
  headline: 'Hello YouTube',
  subheadline: 'Privacy-friendly web analytics made and hosted in Germany — powerful, cookie-free, and fully compliant with GDPR, CCPA, and PECR.',
  mainCTA: {
    content: 'try it for free',
    href: '/feed'
  },
  secondaryCTA: {
    content: 'view live demo',
    href: '#'
  },
  illustration: '/illustration.svg',
  reviews: [
    {
      name: "John Doe",
      designation: "Software Engineer",
      image:
        "https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=3387&q=80",
    },
    {
      name: "Robert Johnson",
      designation: "Product Manager",
      image:
        "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8YXZhdGFyfGVufDB8fDB8fHww&auto=format&fit=crop&w=800&q=60",
    },
    {
      name: "Jane Smith",
      designation: "Data Scientist",
      image:
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NXx8YXZhdGFyfGVufDB8fDB8fHww&auto=format&fit=crop&w=800&q=60",
    },
    {
      name: "Emily Davis",
      designation: "UX Designer",
      image:
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fGF2YXRhcnxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60",
    },
    {
      name: "Tyler Durden",
      designation: "Soap Developer",
      image:
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=3540&q=80",
    }
  ]
}

export default function Hero() {
  return (
    <div className="space-y-12 md:space-y-20 lg:space-y-28 z-50 relative">
      <Navbar />

      <section className="flex flex-col gap-8 lg:gap-11 items-center text-center">
        {/* Headline */}
        <h1 className="text-black dark:text-white text-4xl md:text-6xl lg:text-hero font-medium tracking-tight leading-none xl:max-w-3/4">
          <TextBlurEffect className='text-transparent bg-clip-text bg-gradient-to-b from-black to-black/60 dark:from-white dark:to-white/60'>{settings.headline}</TextBlurEffect>
        </h1>

        {/* Sub-headline */}
        <SlideEffect
          delay={0}
          className="text-sm lg:text-base px-6 sm:px-10 md:px-0 md:max-w-3/4 mx-auto"
        >
          {settings.subheadline}
        </SlideEffect>

        {/* CTA */}
        <SlideEffect
          className="flex flex-col gap-8 md:gap-5 items-center justify-center w-full md:w-fit"
        >
          {/* Buttons */}
          <div className="flex flex-col md:flex-row items-center w-full justify-center gap-3 md:gap-4 mt-1">
            <Link href={settings.mainCTA.href} className="w-full">
              <Button size='lg' className="capitalize w-full hidden lg:flex">
                {settings.mainCTA.content}
                <ArrowRight />
              </Button>

              <Button size='default' className="capitalize w-full flex lg:hidden">
                {settings.mainCTA.content}
                <ArrowRight />
              </Button>
            </Link>

            <Link href={settings.secondaryCTA.href} className="w-full">
              <Button size='lg' className="capitalize w-full hidden lg:flex" variant='secondary'>
                {settings.secondaryCTA.content}
              </Button>

              <Button size='default' className="capitalize w-full flex lg:hidden" variant='secondary'>
                {settings.secondaryCTA.content}
              </Button>
            </Link>
          </div>

          {/* Reviews */}
          <div className="flex flex-col md:flex-row gap-2 md:gap-5 justify-center">
            <AnimatedTooltip items={settings.reviews} />

            <div className="flex flex-col justify-center items-center md:items-start gap-1 md:gap-2">
              <div className="flex gap-px">
                <Star size={16} fill='oklch(0.795 0.184 86.047)' className="text-yellow-500" />
                <Star size={16} fill='oklch(0.795 0.184 86.047)' className="text-yellow-500" />
                <Star size={16} fill='oklch(0.795 0.184 86.047)' className="text-yellow-500" />
                <Star size={16} fill='oklch(0.795 0.184 86.047)' className="text-yellow-500" />
                <Star size={16} fill='oklch(0.795 0.184 86.047)' className="text-yellow-500" />
              </div>

              <span className="text-xs">Trusted by 500+ Customers</span>
            </div>
          </div>
        </SlideEffect>

        {/* Illustration */}
        <SlideEffect className="relative" isSpring={false} duration={1.3}>
          <Image
            src={settings.illustration}
            alt='illustration'
            width={1920}
            height={1080}
            priority
            loading="eager"
          />
          <FadeEffect />
        </SlideEffect>
      </section>
    </div>
  )
}