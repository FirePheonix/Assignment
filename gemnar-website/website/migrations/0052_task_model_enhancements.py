# Generated manually for Task model enhancements

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0051_merge_20250803_0101"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="commission_percentage",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Commission percentage for commission-based tasks",
                max_digits=5,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="experience_details",
            field=models.TextField(
                blank=True,
                help_text="Details about the experience or event access offered",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="gift_card_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Gift card amount for gift card incentives",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="category",
            field=models.CharField(
                choices=[
                    ("POST", "Instagram Post"),
                    ("REEL", "Instagram Reel"),
                    ("STORY", "Instagram Story"),
                    ("VIDEO", "Video Content"),
                    ("BLOG", "Blog Article"),
                    ("REVIEW", "Product Review"),
                    ("UNBOXING", "Unboxing Video"),
                    ("TUTORIAL", "Tutorial"),
                    ("COLLABORATION", "Brand Collaboration"),
                    ("UGC", "User Generated Content"),
                    ("TESTIMONIAL", "Testimonial"),
                    ("LIVESTREAM", "Live Stream"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="genre",
            field=models.CharField(
                choices=[
                    ("BEAUTY", "Beauty & Cosmetics"),
                    ("FASHION", "Fashion & Style"),
                    ("FOOD", "Food & Beverage"),
                    ("FITNESS", "Fitness & Health"),
                    ("TECH", "Technology"),
                    ("TRAVEL", "Travel & Lifestyle"),
                    ("HOME", "Home & Decor"),
                    ("AUTOMOTIVE", "Automotive"),
                    ("GAMING", "Gaming"),
                    ("FINANCE", "Finance & Business"),
                    ("EDUCATION", "Education"),
                    ("ENTERTAINMENT", "Entertainment"),
                    ("SPORTS", "Sports & Recreation"),
                    ("PETS", "Pets & Animals"),
                    ("PARENTING", "Parenting & Family"),
                    ("SUSTAINABLE", "Sustainability & Eco-friendly"),
                    ("LUXURY", "Luxury Goods"),
                    ("B2B", "Business to Business"),
                    ("OTHER", "Other"),
                ],
                max_length=15,
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="incentive_type",
            field=models.CharField(
                choices=[
                    ("NONE", "No Compensation"),
                    ("BARTER", "Product Exchange"),
                    ("PAY", "Monetary Payment"),
                    ("COMMISSION", "Commission Based"),
                    ("EXPOSURE", "Exposure & Credits"),
                    ("GIFT_CARD", "Gift Card"),
                    ("EXPERIENCE", "Experience/Event Access"),
                ],
                max_length=15,
            ),
        ),
    ]
