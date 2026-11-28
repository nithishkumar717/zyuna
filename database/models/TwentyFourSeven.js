const { DataTypes } = require('sequelize');
const sequelize = require('../sequelize');
const BaseModel = require('../BaseModel');

const cache247 = new Map();

class TwentyFourSeven extends BaseModel {
    static init(sequelize) {
        super.init(
            {
                id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
                guildId: { type: DataTypes.STRING, allowNull: false, unique: true },
                voiceChannelId: { type: DataTypes.STRING, allowNull: false },
                textChannelId: { type: DataTypes.STRING, allowNull: true },
                enabled: { type: DataTypes.BOOLEAN, allowNull: false, defaultValue: true },
            },
            {
                sequelize,
                modelName: 'TwentyFourSeven',
                tableName: 'twenty_four_seven',
                timestamps: true,
            }
        );

        return this;
    }

    static async getGuild247(guildId) {
        const key = String(guildId);
        if (cache247.has(key)) {
            return cache247.get(key);
        }

        try {
            const record = await this.findOne({ where: { guildId: key } });
            if (record && record.enabled) {
                const entry = {
                    enabled: true,
                    voiceChannelId: record.voiceChannelId,
                    textChannelId: record.textChannelId || null,
                };
                cache247.set(key, entry);
                return entry;
            }
            const disabled = { enabled: false, voiceChannelId: null, textChannelId: null };
            cache247.set(key, disabled);
            return disabled;
        } catch {
            return { enabled: false, voiceChannelId: null, textChannelId: null };
        }
    }

    static async enable247(guildId, voiceChannelId, textChannelId = null) {
        const key = String(guildId);
        const entry = {
            enabled: true,
            voiceChannelId: String(voiceChannelId),
            textChannelId: textChannelId ? String(textChannelId) : null,
        };
        cache247.set(key, entry);

        try {
            const [record, created] = await this.findOrCreate({
                where: { guildId: key },
                defaults: { guildId: key, ...entry },
            });
            if (!created) {
                await record.update(entry);
            }
        } catch {
            // Cache remains active even if SQLite is temporarily busy
        }

        return entry;
    }

    static async disable247(guildId) {
        const key = String(guildId);
        const disabled = { enabled: false, voiceChannelId: null, textChannelId: null };
        cache247.set(key, disabled);

        try {
            await this.update(
                { enabled: false },
                { where: { guildId: key } }
            );
        } catch {
            // Ignore DB error
        }

        return disabled;
    }

    static async getAllEnabled() {
        try {
            const rows = await this.findAll({ where: { enabled: true } });
            return rows.map((r) => {
                const entry = {
                    guildId: r.guildId,
                    voiceChannelId: r.voiceChannelId,
                    textChannelId: r.textChannelId || null,
                };
                cache247.set(String(r.guildId), { enabled: true, ...entry });
                return entry;
            });
        } catch {
            return [];
        }
    }
}

TwentyFourSeven.init(sequelize);

module.exports = TwentyFourSeven;
