'use client'

import Badge from "@/components/badge"
import Card from "@/components/card"
import SlideEffect from "@/components/slide-effect"
import { PhoneCarousel } from "@/components/mobile-carousel"

const settings = {
  badge: {
    number: 5,
    text: 'AI CREATION SUITE',
  },
  title: 'Create Smarter, Not Harder',
  description:
    'Seamlessly generate high-quality brand photos and videos, design AI-powered influencer mockups, and produce stunning multi-format campaigns — all within one powerful, multimodal platform.',
  card_1: {
    title: 'Generate Brand Videos & Photos',
    content:
      'Produce studio-quality visuals instantly. Generate on-brand videos and photos with AI that understands your aesthetic, tone, and message — no camera crew required.',
  },
  card_2: {
    title: 'AI Influencer Mockups',
    content:
      'Visualize your brand in action with realistic AI influencers. Create lifelike mockups for campaigns, test creative ideas, and see your products come to life in seconds.',
  },
  card_3: {
    title: 'Multi-Modal Powerhouse',
    content:
      'From text to image to video, our multi-model engine handles it all. Generate, edit, and scale content effortlessly — all from one unified, intelligent platform.',
  },
}

const carouselImages = [
  {
    src: 'https://cdn.jsdelivr.net/gh/ishaan-arora-1/videos/public/vid1.mp4',
    alt: 'AI Creation Suite walkthrough 1',
    type: 'video' as const,
  },
  {
    src: 'https://cdn.jsdelivr.net/gh/ishaan-arora-1/videos/public/vid2.mp4',
    alt: 'AI Creation Suite walkthrough 2',
    type: 'video' as const,
  },
  {
    src: 'https://cdn.jsdelivr.net/gh/ishaan-arora-1/videos/public/vid3.mp4',
    alt: 'AI Creation Suite walkthrough 3',
    type: 'video' as const,
  },
]

export default function Features5() {
  return (
    <div className="space-y-6 sm:space-y-7 md:space-y-8 lg:space-y-10 mx-auto text-center">
      {/* Badge */}
      <SlideEffect>
        <Badge number={settings.badge.number} text={settings.badge.text} />
      </SlideEffect>

      {/* Title */}
      <SlideEffect>
        <h2 className="text-2xl md:text-4xl lg:text-header capitalize text-transparent bg-clip-text bg-gradient-to-b from-black to-black/60 dark:from-white dark:to-white/60 font-medium leading-normal">
          {settings.title}
        </h2>
      </SlideEffect>

      {/* Description */}
      <SlideEffect className="px-2 sm:px-10 md:px-0 w-full md:max-w-3/4 mx-auto text-sm lg:text-base">
        {settings.description}
      </SlideEffect>

      {/* Phone Carousel */}
      <SlideEffect direction="top" className="w-full" isSpring={false}>
        <PhoneCarousel images={carouselImages} />
      </SlideEffect>

      {/* Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* card 1 */}
        <SlideEffect direction="top" className="col-span-1 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
              {settings.card_1.title}
            </h3>
            <p>{settings.card_1.content}</p>
          </Card>
        </SlideEffect>

        {/* card 2 */}
        <SlideEffect direction="top" delay={0.2} className="col-span-1 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
              {settings.card_2.title}
            </h3>
            <p>{settings.card_2.content}</p>
          </Card>
        </SlideEffect>

        {/* card 3 */}
        <SlideEffect direction="top" delay={0.3} className="col-span-1 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
              {settings.card_3.title}
            </h3>
            <p>{settings.card_3.content}</p>
          </Card>
        </SlideEffect>
      </div>
    </div>
  )
}
