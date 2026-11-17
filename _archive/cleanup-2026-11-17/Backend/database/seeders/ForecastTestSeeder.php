<?php

namespace Database\Seeders;

use App\Models\Business;
use App\Models\Product;
use App\Models\Review;
use App\Models\SentimentResult;
use Illuminate\Database\Seeder;
use Illuminate\Support\Carbon;

class ForecastTestSeeder extends Seeder
{
    public function run(): void
    {
        // Create a test business
        $business = Business::query()->create([
            'name' => 'Forecast Test Shop',
            'platform' => 'jumia',
            'external_url' => 'https://jumia.com.ng/shop/forecast-test',
        ]);

        // Create a product
        $product = Product::query()->create([
            'business_id' => $business->id,
            'name' => 'Test Product for Forecasting',
        ]);

        // Create 10 weeks of review history (more than the 8-week minimum)
        $startDate = Carbon::parse('2026-06-22');
        $sentiments = [
            ['score' => 0.6, 'label' => 'positive', 'rating' => 5],
            ['score' => 0.5, 'label' => 'positive', 'rating' => 4],
            ['score' => 0.3, 'label' => 'positive', 'rating' => 4],
            ['score' => -0.2, 'label' => 'negative', 'rating' => 2],
            ['score' => 0.0, 'label' => 'neutral', 'rating' => 3],
            ['score' => 0.7, 'label' => 'positive', 'rating' => 5],
            ['score' => 0.4, 'label' => 'positive', 'rating' => 4],
            ['score' => 0.8, 'label' => 'positive', 'rating' => 5],
            ['score' => 0.2, 'label' => 'neutral', 'rating' => 3],
            ['score' => 0.9, 'label' => 'positive', 'rating' => 5],
        ];

        // Create reviews across 10 weeks
        for ($week = 0; $week < 10; $week++) {
            $weekStart = $startDate->clone()->addWeeks($week);

            // Create 3-5 reviews per week
            $reviewsPerWeek = rand(3, 5);
            for ($i = 0; $i < $reviewsPerWeek; $i++) {
                $sentiment = $sentiments[($week * 3 + $i) % count($sentiments)];
                $reviewDate = $weekStart->clone()->addDays(rand(0, 4))->setTime(rand(9, 18), rand(0, 59));

                $review = Review::query()->create([
                    'business_id' => $business->id,
                    'product_id' => $product->id,
                    'source' => 'manual_entry',
                    'raw_text' => "Week {$week} review {$i}: Test review with ".$sentiment['label'].' sentiment.',
                    'star_rating' => $sentiment['rating'],
                    'reviewed_at' => $reviewDate,
                ]);

                SentimentResult::query()->create([
                    'review_id' => $review->id,
                    'label' => $sentiment['label'],
                    'confidence' => rand(85, 99) / 100,
                    'compound_score' => $sentiment['score'],
                    'model_mode' => 'both_loaded',
                    'model_used' => 'general',
                ]);
            }
        }

        echo "✓ Created business (ID: {$business->id}) with 10 weeks of reviews\n";
    }
}
