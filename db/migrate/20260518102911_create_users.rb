class CreateUsers < ActiveRecord::Migration[8.1]
  def change
    create_table :users do |t|
      t.string :govukId
      t.string :apprenticeId
      t.string :colCampaignId

      t.timestamps
    end
  end
end
